#!/usr/bin/env node
// Combined Ollama API provider and grader for promptfoo
//
// Auto-detects mode based on prompt format:
// - Grader mode: Prompt is JSON array [{role, content}, ...]
// - Provider mode: Prompt is plain text
//
// Makes HTTP requests to a local Ollama server
// Configurable via options: host (default localhost), port (default 11434), endpoint (default /api/v1/chat), model (default llama2)

const http = require('http');
const fs = require('fs');
const path = require('path');

const prompt = process.argv[2];
const options = process.argv[3];
const context = process.argv[4];

// Parse options to extract host, port, endpoint, model, and documentRoot
let host = 'localhost'; // Default local host
let port = 11434; // Default Ollama port
let endpoint = '/api/v1/chat'; // Default LM Studio endpoint
let model = 'llama2'; // Default model
let documentRoot = null; // Optional document root for file rendering
if (options && options !== '{}') {
  try {
    const optionsObj = JSON.parse(options);
    if (optionsObj.config) {
      if (optionsObj.config.host) {
        host = optionsObj.config.host;
      }
      if (optionsObj.config.port) {
        port = optionsObj.config.port;
      }
      if (optionsObj.config.endpoint) {
        endpoint = optionsObj.config.endpoint;
      }
      if (optionsObj.config.model) {
        model = optionsObj.config.model;
      }
      if (optionsObj.config.documentRoot) {
        documentRoot = optionsObj.config.documentRoot;
      }
    }
  } catch (e) {
    // If JSON parsing fails, use defaults
  }
}

// Detect mode: if prompt looks like a JSON array, use grader mode
let isGraderMode = false;
try {
  const parsed = JSON.parse(prompt);
  if (Array.isArray(parsed) && parsed.length > 0 && parsed[0].role) {
    isGraderMode = true;
  }
} catch (e) {
  // Not JSON, so provider mode
}

// Helper function to render file content with nested @{filename} references
function renderFile(filePath, relativeRoot, visited = new Set()) {
  const absolutePath = path.resolve(relativeRoot, filePath);
  const normalizedPath = path.normalize(absolutePath);
  
  // Detect circular references
  if (visited.has(normalizedPath)) {
    throw new Error(`Circular reference detected: ${filePath} from ${relativeRoot} (attempted path: ${normalizedPath})`);
  }
  visited.add(normalizedPath);
  
  try {
    if (!fs.existsSync(normalizedPath)) {
      throw new Error(`No file named ${filePath} near ${relativeRoot} (attempted path: ${normalizedPath})`);
    }
    
    let content = fs.readFileSync(normalizedPath, 'utf8');
    const fileDir = path.dirname(normalizedPath);
    
    // Find and replace nested @{filename} references
    const fileRefPattern = /@([^\s\n]+)/g;
    let match;
    const replacements = [];
    
    while ((match = fileRefPattern.exec(content)) !== null) {
      const refFileName = match[1];
      replacements.push({
        fullMatch: match[0],
        fileName: refFileName,
        index: match.index
      });
    }
    
    // Process replacements in reverse order to maintain indices
    for (let i = replacements.length - 1; i >= 0; i--) {
      const replacement = replacements[i];
      try {
        const nestedContent = renderFile(replacement.fileName, fileDir, visited);
        content = content.substring(0, replacement.index) + nestedContent + content.substring(replacement.index + replacement.fullMatch.length);
      } catch (e) {
        throw new Error(`Failed to render ${filePath} from ${relativeRoot} -> ${e.message}`);
      }
    }
    
    return content;
  } catch (e) {
    if (e.message.startsWith('Failed to render')) {
      throw e;
    }
    throw new Error(`Failed to render ${filePath} from ${relativeRoot}: ${e.message}`);
  }
}

// Helper function to render a prompt string by expanding @{filename} references
function renderPrompt(promptText, documentRoot) {
  // Find all @{filename} references in the prompt
  // Match @filename where filename contains path separators and file extensions
  // Stops at whitespace or sentence-ending punctuation
  const fileRefPattern = /@([\w./_-]*\.[a-zA-Z0-9]+)/g;
  let match;
  const replacements = [];
  
  while ((match = fileRefPattern.exec(promptText)) !== null) {
    const refFileName = match[1];
    replacements.push({
      fullMatch: match[0],
      fileName: refFileName,
      index: match.index
    });
  }
  
  // Process replacements in reverse order to maintain indices
  let result = promptText;
  for (let i = replacements.length - 1; i >= 0; i--) {
    const replacement = replacements[i];
    try {
      // If reference contains .windsurf or other absolute-ish paths, resolve from cwd
      // Otherwise (simple relative paths like ../SKILL.md), resolve from documentRoot
      const resolveRoot = replacement.fileName.includes('.windsurf') || replacement.fileName.includes('evals') ? '.' : documentRoot;
      const fileContent = renderFile(replacement.fileName, resolveRoot);
      result = result.substring(0, replacement.index) + fileContent + result.substring(replacement.index + replacement.fullMatch.length);
    } catch (e) {
      throw new Error(`Failed to render ${replacement.fileName}: ${e.message}`);
    }
  }
  
  return result;
}

// Helper function to make HTTP request to Ollama
function callOllama(input, systemPrompt) {
  return new Promise((resolve, reject) => {
    const payloadObj = {
      model: model,
      input: input,
      stream: false
    };
    if (systemPrompt) {
      payloadObj.system_prompt = systemPrompt;
    }
    const payload = JSON.stringify(payloadObj);

    const requestOptions = {
      hostname: host,
      port: port,
      path: endpoint,
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(payload)
      }
    };

    const req = http.request(requestOptions, (res) => {
      let data = '';

      res.on('data', (chunk) => {
        data += chunk;
      });

      res.on('end', () => {
        if (res.statusCode !== 200) {
          reject(new Error(`Ollama API error: ${res.statusCode} - ${data}`));
          return;
        }

        try {
          const response = JSON.parse(data);
          const output = response.output;
          if (Array.isArray(output) && output.length > 0) {
            const messageOutput = output.find(o => o.type === 'message');
            resolve(messageOutput ? messageOutput.content : output[0].content);
          } else {
            reject(new Error('Unexpected Ollama response format'));
          }
        } catch (e) {
          reject(new Error(`Failed to parse Ollama response: ${e.message}`));
        }
      });
    });

    req.on('error', (e) => {
      reject(new Error(`Failed to connect to Ollama at ${host}:${port}${endpoint}: ${e.message}`));
    });

    req.write(payload);
    req.end();
  });
}

async function main() {
  try {
    if (isGraderMode) {
      // ===== GRADER MODE =====
      // Parse the JSON chat message array that promptfoo sends to graders
      let systemMsg, userMsg;
      try {
        const parsed = JSON.parse(prompt);
        const systemMessage = parsed.find(m => m.role === 'system');
        const userMessage = parsed.find(m => m.role === 'user');

        if (systemMessage && userMessage) {
          systemMsg = systemMessage.content;
          userMsg = userMessage.content;
        } else {
          throw new Error('Missing system or user message');
        }
      } catch (e) {
        // Fallback: treat the whole thing as a user message
        systemMsg = 'You are an evaluator. Respond with only valid JSON: {"pass": bool, "score": 0.0-1.0, "reason": "string"}';
        userMsg = prompt;
      }

      const output = await callOllama(userMsg, systemMsg);
      console.log(output);
    } else {
      // ===== PROVIDER MODE =====
      let userPrompt = prompt;
      
      // Render file references if documentRoot is provided
      if (documentRoot) {
        userPrompt = renderPrompt(prompt, documentRoot);
      }
      
      const output = await callOllama(userPrompt);
      console.log(output);
    }
  } catch (error) {
    console.error(error.message);
    process.exit(1);
  }
}

main();
