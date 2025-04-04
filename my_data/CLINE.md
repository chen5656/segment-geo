# Setting up CLINE with Gemini API

This guide will walk you through setting up CLINE with a Gemini API key from Google, adding CLINE to VS Code, configuring the Gemini key for CLINE, and using chat/plan to help with your coding.

## 1. Applying for a Gemini API Key from Google

To use CLINE with the Gemini API, you'll need an API key from Google. Here's how to get one:

1.  **Go to the Google AI Studio website:** [https://makersuite.google.com/app/apikey](https://makersuite.google.com/app/apikey)
2.  **Sign in with your Google account.**
3.  **Create a new API key.** You may need to agree to the terms of service.
4.  **Copy the API key.** You'll need this in the next steps.

**Important:** Treat your API key like a password. Do not share it publicly or commit it to version control.

## 2. Adding CLINE to VS Code

CLINE is a VS Code extension. Here's how to add it:

1.  **Open VS Code.**
2.  **Go to the Extensions Marketplace:** Click on the Extensions icon in the Activity Bar on the side of the window (or press `Ctrl+Shift+X`).
3.  **Search for "CLINE".**
4.  **Find the CLINE extension** (likely named something like "Cline AI Assistant").
5.  **Click "Install".**
6.  **Reload VS Code** if prompted.

## 3. Setting up the Gemini Key for CLINE

Once CLINE is installed, you need to configure it with your Gemini API key:

1.  **Open VS Code settings:** Go to `File > Preferences > Settings` (or press `Ctrl+,`).
2.  **Search for "cline api key".**  This should bring up the CLINE extension settings.
3.  **Enter your Gemini API key** into the appropriate setting field (e.g., "Cline: Gemini Api Key").
4.  **Close the settings tab.** CLINE should now be able to access the Gemini API.

## 4. Using Chat/Plan to Help Your Coding

CLINE provides two main modes for assisting with your coding: Chat and Plan.

*   **Chat:** Use the Chat mode for quick questions, code snippets, debugging help, and general coding assistance.  You can ask CLINE to explain code, suggest improvements, find errors, or generate code based on your prompts.
*   **Plan:** Use the Plan mode for more complex tasks, such as designing a new feature, refactoring existing code, or understanding a large codebase.  In Plan mode, CLINE will work with you to create a detailed plan, breaking down the task into smaller, manageable steps.  You can then execute the plan step-by-step, using CLINE to assist with each step.

**Example Usage:**

*   **Chat:** "How do I reverse a string in JavaScript?"
*   **Chat:** "Explain this Python code: `def my_function(x): return x + 1`"
*   **Plan:** "Refactor this class to use dependency injection."
*   **Plan:** "Create a new API endpoint that returns a list of users."

**Tips for Effective Prompts:**

*   Be clear and specific in your requests.
*   Provide context when necessary.
*   Use code examples to illustrate your points.
*   Ask follow-up questions to clarify the results.

By following these steps, you can set up CLINE with the Gemini API and start using it to enhance your coding workflow.
