# ---- Base python ----
FROM python:3.10-alpine3.16 AS base
RUN apk add build-base libffi-dev
WORKDIR /app

# ---- Dependencies ----
FROM base AS dependencies  
COPY src/requirements.txt ./
# install app dependencies
RUN pip install -r requirements.txt

# ---- Copy Files/Build ----
FROM dependencies AS build  
COPY src ./
# Build / Compile if required

# --- Release with Alpine ----
FROM python:3.10-alpine3.16 AS release  
# Create app directory
WORKDIR /app
COPY --from=dependencies /app/requirements.txt ./
COPY --from=dependencies /root/.cache /root/.cache
# Install app dependencies
RUN pip install -r requirements.txt
COPY --from=build /app/ ./
COPY package.json ./
ENTRYPOINT ["python", "app.py"]
