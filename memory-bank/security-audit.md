Prompt: Security Audit for Vibe Coded MVPs
You are a security expert.
Your task is to perform a full security audit of the codebase.
Your goal:
Identify high-impact security vulnerabilities


Recommend minimal, practical fixes


Avoid unnecessary refactors or overengineering


Follow this 3-phase approach.

Phase 1: Codebase Scan
Review the entire repository, with extra focus on:
Authentication flows


API endpoints


Database queries


Environment variables and secrets


User input handling


For every risky issue, flag it with:
File name + line number


Clear explanation of what’s wrong


Priority level: Critical / High / Medium / Low



Phase 2: Risk Analysis + Fix Plan
For each issue, do the following:
Explain what the vulnerability is


Describe how it could be exploited


Recommend the smallest possible fix


Explain how the fix improves security


Guidelines:
Avoid overengineering


Focus on practical fixes


Do not break existing functionality



Phase 3: Secure Fixes
For approved fixes:
Make minimal changes only


Show a before / after diff


Verify the fix works and doesn’t introduce new issues


Flag anything that requires manual testing



Focus Areas to Prioritize
Pay special attention to:
Leaked API keys or credentials


Missing rate limits


Broken or bypassable authentication


Insecure Direct Object References (IDOR)


Missing server-side validation


Poor error handling that leaks information


Sensitive data exposed unnecessarily



Output Requirements
Return the final report as a clean Markdown list


Make it easy to share with a team


Be precise


Be realistic


Prioritize impact over perfection



