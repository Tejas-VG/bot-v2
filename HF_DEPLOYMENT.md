# Deployment Guide: Hugging Face Spaces (Docker)

This guide explains how to deploy your Rasa chatbot backend (Rasa Server + Custom Action Server) to a **Hugging Face Space** for free.

---

## Step 1: Create a Hugging Face Space

1. Go to [Hugging Face](https://huggingface.co/) and log in or sign up.
2. Click on your profile icon in the top right and select **New Space**.
3. Configure the Space:
   * **Space Name**: `medi-bot` (or any name you prefer).
   * **License**: Choose any license (e.g. `mit`).
   * **Select the Space SDK**: Choose **Docker**.
   * **Docker Template**: Choose **Blank**.
   * **Space Hardware**: Choose the default free CPU basic tier (2 vCPU, 16 GB RAM - which is plenty for Rasa!).
   * **Visibility**: Public (recommended so your web frontend can access it).
4. Click **Create Space**.

---

## Step 2: Push your Code to the Hugging Face Git Repository

When you create a Space, Hugging Face creates a Git repository for you. You can push your code directly to this repository to deploy the bot.

In your local command prompt/terminal, run the following commands (replace `username` with your Hugging Face username):

```bash
# 1. Add Hugging Face as a remote repository
git remote add hf https://huggingface.co/spaces/username/medi-bot

# 2. Push the code to Hugging Face (this will start the build)
git push hf main --force
```

*Note: You may be prompted to enter your Hugging Face username and password. For the password, you must use a **Hugging Face Access Token** with **Write** permission. You can generate one in your account settings under [Access Tokens](https://huggingface.co/settings/tokens).*

---

## Step 3: Wait for Build to Complete

1. Open your Space page on Hugging Face.
2. You will see a status bar showing the build logs.
3. Once the build finishes, the status will turn green and say **Running**.
4. Since Rasa is a backend API, the Space UI might display a blank screen or a "404 Not Found" message (which is expected because there is no frontend inside the Docker container). 
   * To verify it is running, you can click on **Logs** at the top of the page. You should see both `rasa run actions` and `rasa run` logs running successfully.

---

## Step 4: Connect your Web UI (Frontend)

1. Your Space API will be accessible via a public URL formatted as:
   `https://<username>-<space-name>.hf.space`
   *(For example: `https://tejas-vg-medi-bot.hf.space`)*
2. Open your frontend `index.html` file.
3. Update the `socketUrl` or `data-websocket-url` to point to your Hugging Face Space URL:
   ```javascript
   socketUrl: "https://<username>-<space-name>.hf.space/",
   ```
4. Save and deploy your frontend (e.g. to **Vercel**).

*Note: Hugging Face automatically handles HTTPS, so make sure to use `https://` instead of `http://` when connecting from your frontend!*
