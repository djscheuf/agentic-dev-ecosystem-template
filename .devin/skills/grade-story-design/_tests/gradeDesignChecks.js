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

function _pullVarFromAssertConfig(context, varName) {
    return context.vars?.assert_config?.[varName] || undefined;
}

function hasExpectedFailingSections(output, context) {
    const expectedFailingSections = _pullVarFromAssertConfig(context, 'expected_failing_sections');
    if (!expectedFailingSections || !Array.isArray(expectedFailingSections) || expectedFailingSections.length === 0) {
        return {
            pass: false,
            score: 0,
            reason: 'Missing Assert Config: expected_failing_sections[]'
        };
    }

    const scoreFloor = _pullVarFromAssertConfig(context, 'score_floor');
    if (!scoreFloor) {
        return {
            pass: false,
            score: 0,
            reason: 'Missing Assert Config: score_floor (Number)'
        };
    }

    const json = _parseJsonOutput(output);
    if (!json) {
        return {
            pass: false,
            score: 0,
            reason: 'Invalid JSON output'
        };
    }

    let errors=[];
    expectedFailingSections.forEach(section => {
        const sectionData = json[section];
        if (!sectionData || !sectionData.score) {
            errors.push(`Missing section: ${section}`);
        }
        if (sectionData.score > scoreFloor) {
            errors.push(`Section ${section} should have score <= ${scoreFloor} but got ${sectionData.score}`);
        }
    });

    if (errors.length > 0) {
        return {
            pass: false,
            score: 0,
            reason: errors.join('; ')
        };
    }

    return {
        pass: true,
        score: 1,
        reason: 'All expected failing sections have scores under score_floor'
    };
}


const VALID_SCORES = [0,1,2,3];
function allScoresWithinBounds(output){
    const json = _parseJsonOutput(output);
    if (!json) {
        return {
            pass: false,
            score: 0,
            reason: 'Invalid JSON output'
        };
    }

    let errors = [];
    Object.keys(json).forEach(section => {
        if(!json[section].score) {
            errors.push(`Section ${section} has no score`);
            return;
        }
        if(!VALID_SCORES.includes(json[section].score)) {
            errors.push(`Section ${section} has invalid score: ${json[section].score}`);
            return;
        }
    });
    
    if(errors.length > 0) {
        return {
            pass: false,
            score: 0,
            reason: errors.join('; ')
        };
    }
    
    return {
        pass: true,
        score: 1,
        reason: 'All scores are within valid bounds'
    };
}

module.exports = { hasExpectedFailingSections, allScoresWithinBounds };
