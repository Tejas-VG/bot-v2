FROM rasa/rasa:2.8.1-full

USER root
WORKDIR /app

# The model was trained locally with scipy >= 1.8.0 (which has scipy.sparse._coo).
# The rasa:2.8.1-full base image ships with scipy < 1.8.0, causing load failure.
# We UPGRADE scipy using the venv's pip explicitly to override the image's version.
RUN /opt/venv/bin/pip install --no-cache-dir "scipy==1.9.3"

# Copy project files
COPY ./api /app
COPY ./start.sh /app/start.sh
RUN chmod +x /app/start.sh

ENV HOME=/app
ENV PYTHONPATH=/app
ENV SANIC_HOST=0.0.0.0

RUN chown -R 1000:0 /app && chmod -R 775 /app

EXPOSE 7860
USER 1000
ENTRYPOINT []
CMD ["/bin/bash", "/app/start.sh"]
