#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

/**
 * Recreate conversation logs from existing turn files
 */

const workspaceRoot = process.cwd();
const auditRoot = path.join(workspaceRoot, '.audit');
const turnsDir = path.join(auditRoot, 'turns');
const conversationsDir = path.join(auditRoot, 'conversations');

// Parse JSONL transcript
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
function extractCurrentTurn(allSteps) {
  let lastUserInputIndex = -1;
  for (let i = allSteps.length - 1; i >= 0; i--) {
    if (allSteps[i].type === 'user_input') {
      lastUserInputIndex = i;
      break;
    }
  }
  
  if (lastUserInputIndex === -1) {
    return allSteps;
  }
  
  return allSteps.slice(lastUserInputIndex);
}

// Convert transcript steps to markdown
function stepsToMarkdown(steps) {
  let markdown = '';
  
  for (const step of steps) {
    if (step.type === 'user_input' && step.user_input) {
      markdown += `## User\n\n`;
      markdown += `${step.user_input.user_response || step.user_input.text || '(No text)'}\n\n`;
      
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
function main() {
  console.log('Recreating conversation logs from turn files...\n');
  
  // Ensure conversations directory exists
  fs.mkdirSync(conversationsDir, { recursive: true });
  
  // Get all turn files
  const turnFiles = fs.readdirSync(turnsDir)
    .filter(f => f.endsWith('.jsonl'))
    .sort(); // Sort to process in chronological order
  
  console.log(`Found ${turnFiles.length} turn files\n`);
  
  // Group turn files by trajectory_id
  const trajectories = {};
  
  for (const turnFile of turnFiles) {
    const [trajectoryId, executionId] = turnFile.replace('.jsonl', '').split('_');
    
    if (!trajectories[trajectoryId]) {
      trajectories[trajectoryId] = [];
    }
    
    trajectories[trajectoryId].push({
      filename: turnFile,
      executionId,
      path: path.join(turnsDir, turnFile)
    });
  }
  
  console.log(`Processing ${Object.keys(trajectories).length} conversations:\n`);
  
  // Process each trajectory
  for (const [trajectoryId, turns] of Object.entries(trajectories)) {
    console.log(`\nConversation: ${trajectoryId}`);
    console.log(`  Turns: ${turns.length}`);
    
    let conversationMarkdown = '';
    let firstTimestamp = null;
    
    // Process each turn in order
    for (let i = 0; i < turns.length; i++) {
      const turn = turns[i];
      console.log(`  Processing turn ${i + 1}/${turns.length}: ${turn.filename}`);
      
      // Parse the full transcript
      const allSteps = parseTranscript(turn.path);
      
      // Get first timestamp from first turn
      if (i === 0) {
        firstTimestamp = getFirstTimestamp(allSteps);
      }
      
      // Extract only the current turn's steps
      const currentTurnSteps = extractCurrentTurn(allSteps);
      
      // Convert to markdown
      const turnMarkdown = stepsToMarkdown(currentTurnSteps);
      
      // Append to conversation
      if (i === 0) {
        // First turn - create header
        conversationMarkdown = `# Conversation: ${trajectoryId}\n\n`;
        conversationMarkdown += `**Started:** ${firstTimestamp}\n\n`;
        conversationMarkdown += `---\n\n`;
        conversationMarkdown += turnMarkdown;
      } else {
        // Subsequent turns - add separator
        conversationMarkdown += '\n---\n\n';
        conversationMarkdown += turnMarkdown;
      }
    }
    
    // Write conversation file
    const conversationPath = path.join(conversationsDir, `${trajectoryId}.md`);
    fs.writeFileSync(conversationPath, conversationMarkdown, 'utf-8');
    console.log(`  ✓ Created: ${trajectoryId}.md`);
  }
  
  console.log('\n✓ All conversations recreated successfully!');
}

main();
