# Eval Driven Development
Think TDD for your AI Prompts

Leveraging Promptfoo for evals on each of the core skills. 

## Structure
Adding a `_tests` directory to each skill with example inputs and expected outputs.
Adding a `{skillname}.tests.yaml` file to each skill with the test cases. 
Invoked with `npm run test {skillname}.tests.yaml`


## One conversion on the skills
Need to convert json 'schema' file to actualy schema:
Use https://jsonjson.com/json-to-schema

Existing '_schemas_' were more examples, so renamed to '{name}.example.json', and used the examples to 
create the schema. using the url above.