/**
 * Custom evaluation script for promptfoo
 * Called directly from promptfooconfig.yaml using: file://eval-script.js:functionName
 *
 * Each function receives (output, context) where output is the LLM response string.
 * Functions must return a boolean, number, or { pass, score, reason } object.
 */

/**
 * Check if the response contains code formatting (fenced blocks or inline backticks)
 */
function hasCodeFormatting(output) {
  const hasFencedBlock = /```[\s\S]*?```/.test(output);
  const hasInlineCode = /`[^`]+`/.test(output);
  return hasFencedBlock || hasInlineCode;
}

/**
 * Check if the response provides an explanation (not just a list of facts)
 */
function explainsWhy(output) {
  const explanationIndicators = [
    'because', 'reason', 'why', 'purpose', 'intended to', 'designed to',
    'means that', 'this allows', 'this prevents',
    'performs', 'converts', 'coercion', 'unlike', 'whereas', 'which means',
    'ensures', 'checks', 'validates', 'since', 'uses', 'this means',
    'will ', 'allows ', 'prevents ', 'returns ',
  ];
  return explanationIndicators.some(indicator => output.toLowerCase().includes(indicator));
}

/**
 * Check if response mentions best practices, caveats, or practical guidance
 */
function mentionsBestPractices(output) {
  const practiceIndicators = [
    'best practice', 'edge case', 'consider', 'note', 'warning', 'however',
    'recommend', 'avoid', 'prefer', 'always', 'never', 'make sure',
    'pattern', 'approach', 'important', 'useful',
  ];
  return practiceIndicators.some(indicator => output.toLowerCase().includes(indicator));
}

/**
 * Check response length is within a reasonable range (50–500 words)
 */
function isConcise(output) {
  const wordCount = output.split(/\s+/).filter(Boolean).length;
  return wordCount >= 50 && wordCount <= 500;
}

function matchesSchema(output, schema) {
  // TODO: Implement schema validation
  return true;
}

module.exports = { hasCodeFormatting, explainsWhy, mentionsBestPractices, isConcise, matchesSchema };
