#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const readline = require('readline');

/**
 * Cascade Audit Logger
 * Captures conversation turns and builds markdown history documents
 */

const MAX_LOG_SIZE_MB = 5;
const MAX_LOG_FILES = 3;

// Simple logger with rotation
function setupLogger(workspaceRoot) {
  const logsDir = path.join(workspaceRoot, '.audit', 'logs');
  fs.mkdirSync(logsDir, { recursive: true });
  
  const logFile = path.join(logsDir, 'audit-logger.log');
  
  // Check if rotation is needed
  if (fs.existsSync(logFile)) {
    const stats = fs.statSync(logFile);
    const sizeMB = stats.size / (1024 * 1024);
    
    if (sizeMB > MAX_LOG_SIZE_MB) {
      rotateLogFiles(logsDir, logFile);
    }
  }
  
  return {
    log: (message) => {
      const timestamp = new Date().toISOString();
      const logLine = `[${timestamp}] ${message}\n`;
      fs.appendFileSync(logFile, logLine, 'utf-8');
    },
    error: (message, error) => {
      const timestamp = new Date().toISOString();
      const logLine = `[${timestamp}] ERROR: ${message}\n${error ? error.stack : ''}\n`;
      fs.appendFileSync(logFile, logLine, 'utf-8');
    }
  };
}

// Rotate log files, keeping only MAX_LOG_FILES
function rotateLogFiles(logsDir, currentLog) {
  // Shift existing rotated logs
  for (let i = MAX_LOG_FILES - 1; i > 0; i--) {
    const oldFile = path.join(logsDir, `audit-logger.log.${i}`);
    const newFile = path.join(logsDir, `audit-logger.log.${i + 1}`);
    
    if (fs.existsSync(oldFile)) {
      if (i === MAX_LOG_FILES - 1) {
        fs.unlinkSync(oldFile); // Delete oldest
      } else {
        fs.renameSync(oldFile, newFile);
      }
    }
  }
  
  // Rotate current log to .1
  const rotatedLog = path.join(logsDir, 'audit-logger.log.1');
  fs.renameSync(currentLog, rotatedLog);
}

// Read hook input from stdin
async function readStdin() {
  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
    terminal: false
  });

  let input = '';
  for await (const line of rl) {
    input += line;
  }
  return JSON.parse(input);
}

// Format timestamp as YYYYmmDDHHMM
function formatTimestamp(isoTimestamp) {
  const date = new Date(isoTimestamp);
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  const hours = String(date.getHours()).padStart(2, '0');
  const minutes = String(date.getMinutes()).padStart(2, '0');
  return `${year}${month}${day}${hours}${minutes}`;
}

// Parse JSONL transcript and extract conversation data
function parseTranscript(transcriptPath) {
  const content = fs.readFileSync(transcriptPath, 'utf-8');
  const lines = content.trim().split('\n');
  const steps = lines.map(line => JSON.parse(line));
  return steps;
}

// Get first timestamp from transcript
function getFirstTimestamp(steps) {
  if (steps.length > 0 && steps[0].timestamp) {
    return steps[0].timestamp;
  }
  return new Date().toISOString();
}

// Extract only the current turn from the full conversation history
// A turn starts with a user_input, so we find the last user_input and take steps from there
function extractCurrentTurn(allSteps) {
  // Find the index of the last user_input
  let lastUserInputIndex = -1;
  for (let i = allSteps.length - 1; i >= 0; i--) {
    if (allSteps[i].type === 'user_input') {
      lastUserInputIndex = i;
      break;
    }
  }
  
  // If no user_input found, return all steps (shouldn't happen)
  if (lastUserInputIndex === -1) {
    return allSteps;
  }
  
  // Return steps from the last user_input onwards
  return allSteps.slice(lastUserInputIndex);
}

// Convert transcript steps to markdown
function stepsToMarkdown(steps) {
  let markdown = '';
  
  for (const step of steps) {
    if (step.type === 'user_input' && step.user_input) {
      markdown += `## User\n\n`;
      markdown += `${step.user_input.user_response || step.user_input.text || '(No text)'}\n\n`;
      
      // Show applied rules if any
      if (step.user_input.rules_applied) {
        const allRules = [
          ...(step.user_input.rules_applied.always_on || []),
          ...(step.user_input.rules_applied.manual || [])
        ];
        if (allRules.length > 0) {
          markdown += `*Rules applied: ${allRules.join(', ')}*\n\n`;
        }
      }
    } else if (step.type === 'planner_response' && step.planner_response) {
      markdown += `## Agent\n\n`;
      markdown += `${step.planner_response.response}\n\n`;
    } else if (step.type === 'code_action' && step.code_action) {
      markdown += `### Action: Code Edit\n\n`;
      markdown += `**File:** \`${step.code_action.path}\`\n\n`;
      
      if (step.code_action.explanation) {
        markdown += `**Explanation:** ${step.code_action.explanation}\n\n`;
      }
      
      if (step.code_action.new_content) {
        markdown += `<details>\n<summary>New content</summary>\n\n\`\`\`\n${step.code_action.new_content}\n\`\`\`\n</details>\n\n`;
      }
    } else if (step.type === 'command_action' && step.command_action) {
      markdown += `### Action: Command\n\n`;
      markdown += `\`\`\`bash\n${step.command_action.command_line}\n\`\`\`\n\n`;
      
      if (step.command_action.output) {
        markdown += `<details>\n<summary>Output</summary>\n\n\`\`\`\n${step.command_action.output}\n\`\`\`\n</details>\n\n`;
      }
    } else if (step.type === 'read_action' && step.read_action) {
      markdown += `### Action: Read File\n\n`;
      markdown += `**File:** \`${step.read_action.path}\`\n\n`;
    } else if (step.type === 'search_action' && step.search_action) {
      markdown += `### Action: Search\n\n`;
      markdown += `**Query:** ${step.search_action.query}\n\n`;
    } else if (step.type === 'tool_use' && step.tool_use) {
      markdown += `### Action: Tool Use\n\n`;
      markdown += `**Tool:** ${step.tool_use.tool_name}\n\n`;
    }
  }
  
  return markdown;
}

// Main execution
async function main() {
  const workspaceRoot = process.cwd();
  const logger = setupLogger(workspaceRoot);
  
  try {
    logger.log('Hook invoked: post_cascade_response_with_transcript');
    
    // Read hook input
    const hookData = await readStdin();
    const { trajectory_id, execution_id, timestamp, tool_info } = hookData;
    const { transcript_path } = tool_info;

    logger.log(`Processing trajectory: ${trajectory_id}, execution: ${execution_id}`);
    
    // Create audit directories
    const auditRoot = path.join(workspaceRoot, '.audit');
    const turnsDir = path.join(auditRoot, 'turns');
    const conversationsDir = path.join(auditRoot, 'conversations');
    
    fs.mkdirSync(turnsDir, { recursive: true });
    fs.mkdirSync(conversationsDir, { recursive: true });

    // Parse transcript
    logger.log(`Reading transcript from: ${transcript_path}`);
    const allSteps = parseTranscript(transcript_path);
    logger.log(`Parsed ${allSteps.length} total steps from transcript`);
    
    // Extract only the current turn
    const currentTurnSteps = extractCurrentTurn(allSteps);
    logger.log(`Extracted ${currentTurnSteps.length} steps for current turn`);
    
    const firstTimestamp = getFirstTimestamp(allSteps);

    // Save turn JSONL
    const turnFilename = `${trajectory_id}_${execution_id}.jsonl`;
    const turnPath = path.join(turnsDir, turnFilename);
    fs.copyFileSync(transcript_path, turnPath);
    logger.log(`Saved turn JSONL: ${turnFilename}`);

    // Build/update markdown conversation history
    const conversationFilename = `${trajectory_id}.md`;
    const conversationPath = path.join(conversationsDir, conversationFilename);
    
    // Generate markdown from current turn only
    const newMarkdown = stepsToMarkdown(currentTurnSteps);
    
    // Check if conversation file exists
    let fullMarkdown = '';
    if (fs.existsSync(conversationPath)) {
      // Append to existing conversation
      logger.log(`Updating existing conversation: ${conversationFilename}`);
      const existingContent = fs.readFileSync(conversationPath, 'utf-8');
      fullMarkdown = existingContent + '\n---\n\n' + newMarkdown;
    } else {
      // Create new conversation file with header
      logger.log(`Creating new conversation: ${conversationFilename}`);
      fullMarkdown = `# Conversation: ${trajectory_id}\n\n`;
      fullMarkdown += `**Started:** ${firstTimestamp}\n\n`;
      fullMarkdown += `---\n\n`;
      fullMarkdown += newMarkdown;
    }
    
    fs.writeFileSync(conversationPath, fullMarkdown, 'utf-8');
    logger.log(`Successfully saved conversation: ${conversationFilename}`);

    // Log success to stdout (optional, only if show_output is true)
    console.log(`Audit logged: ${conversationFilename}`);
    
  } catch (error) {
    logger.error('Audit logger failed', error);
    console.error('Audit logger error:', error.message);
    process.exit(1);
  }
}

main();
