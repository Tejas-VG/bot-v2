FROM rasa/rasa:2.8.1-full

# Switch to root to set up directory and permissions
USER root

# Set the working directory
WORKDIR /app

# Copy the contents of the api folder to /app
COPY ./api /app

# Set environment variables
ENV HOME=/app
ENV PYTHONPATH=/app

# Ensure permissions are correct for user 1000 (Hugging Face default) and group 0
RUN chown -R 1000:0 /app && chmod -R 775 /app

# Expose the Hugging Face port
EXPOSE 7860

# Switch to Hugging Face user
USER 1000

# Start action server in background, then start Rasa server in foreground on port 7860
CMD rasa run actions --actions actions --port 5055 --host 0.0.0.0 & rasa run -m models --enable-api --cors "*" --port 7860 --host 0.0.0.0
