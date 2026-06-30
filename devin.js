#!/usr/bin/env node
// Combined Devin CLI provider and grader for promptfoo
//
// Auto-detects mode based on prompt format:
// - Grader mode: Prompt is JSON array [{role, content}, ...]
// - Provider mode: Prompt is plain text
//
// Grader: Parses JSON chat array, concatenates system + user messages (no --system-prompt)
// Provider: Passes prompt directly to Devin CLI

const { spawnSync } = require('child_process');

const prompt = process.argv[2];
const options = process.argv[3];
const context = process.argv[4];

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

if (isGraderMode) {
  // ===== GRADER MODE =====
  // Parse OPTIONS to get model from config
  let model = 'SWE-1.6'; // Default model
  if (options && options !== '{}') {
    try {
      const optionsObj = JSON.parse(options);
      if (optionsObj.config && optionsObj.config.model) {
        model = optionsObj.config.model;
      }
    } catch (e) {
      // If JSON parsing fails, use default
      model = 'SWE-1.6';
    }
  }

  // Parse the JSON chat message array that promptfoo sends to graders
  let systemMsg, userMsg;
  try {
    const messages = JSON.parse(prompt);
    const systemMessage = messages.find(m => m.role === 'system');
    const userMessage = messages.find(m => m.role === 'user');

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

  // Combine system and user into one prompt (Devin has no --system-prompt)
  const fullPrompt = `${systemMsg}\n\n${userMsg}`;

  const result = spawnSync('devin', ['-p', '--model', model, '--', fullPrompt], {
    encoding: 'utf8',
    stdio: ['pipe', 'pipe', 'pipe']
  });

  if (result.error) {
    console.error(result.error.message);
    process.exit(1);
  }

  if (result.status !== 0) {
    console.error(result.stdout || result.stderr);
    process.exit(result.status || 1);
  }

  console.log(result.stdout);
} else {
  // ===== PROVIDER MODE =====
  // Parse OPTIONS to get model from config
  let model = 'SWE-1.6'; // Default model
  if (options && options !== '{}') {
    try {
      const optionsObj = JSON.parse(options);
      if (optionsObj.config && optionsObj.config.model) {
        model = optionsObj.config.model;
      }
    } catch (e) {
      // If JSON parsing fails, use default
      model = 'SWE-1.6';
    }
  }

  // Call devin cli with single-turn mode and specified model
  const result = spawnSync('devin', ['-p', '--permission-mode', 'auto', '--model', model, '--', prompt], {
    encoding: 'utf8',
    stdio: ['pipe', 'pipe', 'pipe']
  });

  if (result.error) {
    console.error(result.error.message);
    process.exit(1);
  }

  if (result.status !== 0) {
    console.error(result.stdout || result.stderr);
    process.exit(result.status || 1);
  }

  console.log(result.stdout);
}
