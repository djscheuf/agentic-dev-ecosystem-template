/**
 * Custom evaluation script for promptfoo
 * Called directly from promptfooconfig.yaml using: file://eval-script.js:functionName
 *
 * Each function receives (output, context) where output is the LLM response string.
 * Functions must return a boolean, number, or { pass, score, reason } object.
 */

function _parseJsonOutput(output) {
    try {

        const jsonMatch = output.match(/```json\s*([\s\S]*?)\s*```/);
      if (jsonMatch) {
        output = jsonMatch[1].trim();
      }

        return JSON.parse(output);
    } catch (error) {
        return null;
    }
}

const ADR_AC_BasisPattern = /ADR-\d+|Acceptance Criteria|Criterion/i;
const Audit_CodePath_BasisPattern = /Audit|src\/[a-zA-Z0-9\/_\-\.]+\.(ts|tsx|cs|json)/i;


function hasSoundDecisionBasis(output) {
    // TODO: Implement decision basis check
    const parsedOutput = _parseJsonOutput(output);
    if (!parsedOutput) {
        return {
            pass: false,
            score: 0,
            reason: 'Output does not contain valid JSON'
        };
    }

    const totalDecisions = parsedOutput.architectural_decisions.length;
    let decisionsWithBasis = 0;


    let decisionsWithoutBasis = [];

    parsedOutput.architectural_decisions.forEach(decision => {
        // Check if decision has a sound basis
        if (decision.basis) {
            const hasValidBasisPattern = ADR_AC_BasisPattern.test(decision.basis) || Audit_CodePath_BasisPattern.test(decision.basis);
            if (hasValidBasisPattern) {
                decisionsWithBasis++;
            } else {
                decisionsWithoutBasis.push(decision);
            }
        }
    });

    if (decisionsWithoutBasis.length > 0) {
        return {
            pass: false,
            score: 0,
            reason: `Found ${decisionsWithoutBasis.length} decisions without sound basis. Review Decisions: ${decisionsWithoutBasis.map(d => d.decision).join(', ')}`
        };
    }


    return {
        pass: true,
        score: 1,
        reason: 'All decisions have sound basis in either ADRs, AC, or existing code.'
    };
}

module.exports = { hasSoundDecisionBasis };
