Process: 
1. Review provided story. 
2. convert to structured user story format
	1. Description
	2. AC
		1. JTBD, Persona Served
	3. Target Persona
	4. What value with Target Persona recieve when complete?
		- Where(In what system) will this _value_ be _delivered_?
	5. Tech notes
	6. Reference material
3. Validate Extraction
	1. Match Schema
	2. Has AC, Target PErsona, Value
	3. Has JTBDs
4. expand AC?
	1. Each has Persona, JTBD (in Verb Object Context)
	2. Each expressed in Gherkin format
	3. Each has identified Persona
	4. ensure HAppy Path, bounday, and error handling cases present
	5. 
5. confirm INVEST
	1. Independent 
		1. Does this change depend on functionality that does not yet exist in the application?
		2. Can the entire value of the story be captured by the expected scope?
	2. Negotiable - less important for AI
	3. Valuable
		1. For the targetted persona, when does this become valuable? What is the kind of value? 
			1. Awareness?
			2. Use?
			3. Action?
	4. Estimable - Irrelevant
	5. Small
		1. Do the changes necessary for this story span beyond those areas directly related to it?
		2. Does it handle just 1 workflow step for the cheif user persona?
	6. Testable
		1. Can each AC be independently verified, without depending on functionality that does not yet exist in the app?
