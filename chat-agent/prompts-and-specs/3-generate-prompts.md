The following was feed into opanai, model o1, with reasoning level set to high:
https://platform.openai.com/chat/edit?models=o1

Take the generated specification and draft a detailed, step-by-step blueprint for building this project. Then, once you have a solid plan, break it down into small, iterative chunks that build on each other. Look at these chunks and then go another round to break it into small steps. Review the results and make sure that the steps are small enough to be implemented safely with strong testing, but big enough to move the project forward. Iterate until you feel that the steps are right sized for this project.

From here you should have the foundation to provide a series of prompts for a code-generation LLM that will implement each step following test-driven development practices--i.e., TDD. Prioritize best practices, incremental progress, and early testing, ensuring no big jumps in complexity at any stage. Make sure that each prompt builds on the previous prompts, and ends with wiring things together. There should be no hanging or orphaned code that isn't integrated into a previous step.
Since we are using TDD, prompts should be writtn in sets of two: one for the test and one for the implementation. The test prompt should describe the test in detail, including any setup or teardown needed, and the implementation prompt should describe how to implement the feature in a way that passes the test. 

Make sure and separate each prompt section. Use markdown--output raw markdown. Each prompt should be tagged as text using code tags. The goal is to output prompts, but context, etc is important as well.

<spec.md here>

o1 cost: $0.71
2m2s
15.6kt input
7,863t output (6327t text, 1536t reasoning)

The full o1 model output is in o1-output.md, some of which was then copied
to prompt-plan.md.
