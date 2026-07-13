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
 * Check response length is within a reasonable range (50–500 words)
 */
function isConcise(output) {
  const wordCount = output.split(/\s+/).filter(Boolean).length;
  return wordCount >= 50 && wordCount <= 500;
}

// interface GradingResult {
//   pass: boolean;
//   score: number;
//   reason: string;
//   componentResults?: GradingResult[];
// }

function matchesSchema(output, context) {
  
  const schemaPath = context.config.schemaPath;
  
  if (!schemaPath) {
    return {
      pass: false,
      score: 0,
      reason: 'Schema path not provided',
    };
  }
  
  let jsonObject;

  try {
    const jsonMatch = output.match(/```json\s*([\s\S]*?)\s*```/);
    if (!jsonMatch) {
      return {
        pass: false,
        score: 0,
        reason: 'No JSON code block found in output',
      };
    }
    jsonObject = JSON.parse(jsonMatch[1]);
  } catch (e) {
    return {
      pass: false,
      score: 0,
      reason: `Failed to parse JSON from output: ${e.message}`,
    };
  }

  const Ajv = require("ajv")
  const schema = require(schemaPath)
  
  // console.log("output", output)
  // console.log("schema", JSON.stringify(schema, null, 2))
  // console.log("jsonObject", JSON.stringify(jsonObject, null, 2))

  const ajv = new Ajv()
  const validate = ajv.compile(schema)
  const valid = validate(jsonObject)
  
  // console.log("valid", valid)
  // console.log("errors", JSON.stringify(validate.errors, null, 2))
  
  if (!valid) {
    return {
      pass: false,
      score: 0,
      reason: `JSON does not match schema: ${validate.errors.map(e => e.message).join(', ')}`,
    };
  }


  return true;
}

module.exports = { hasCodeFormatting, explainsWhy, isConcise, matchesSchema };
