#FROM maven:3.9.6-eclipse-temurin-17 AS build
#WORKDIR /app
#COPY pom.xml .
#COPY src ./src
#RUN mvn clean package -DskipTests


#run-time only dockerfile
#compile in azure-pipeline ( incl a task there to compile parallely)


# This Dockerfile is optimized for a pipeline build.
# It expects the JAR file to have been created by a previous step (like the Maven task).
FROM eclipse-temurin:17-jre-alpine

# Set the working directory inside the container
WORKDIR /app

# Copy the JAR from the build context's 'target' directory into the image
# This works because the pipeline's Maven task creates the 'target' directory before this runs.
COPY target/*.jar app.jar

# Expose the port the application runs on
EXPOSE 8080

# The command to run the application when the container starts
ENTRYPOINT ["java", "-jar", "app.jar"]

# disable step 1 when running in pipeline since pipeline does the mvn clean package on
#its own to decrease time usage.
#FROM maven:3.9.6-eclipse-temurin-17 AS build
#WORKDIR /app
#COPY . .
#RUN mvn clean package -DskipTests
#
## Step 2: Runtime stage
#FROM eclipse-temurin:17-jre-alpine
#WORKDIR /app
#COPY --from=build /app/target/*.jar app.jar
#EXPOSE 8080
#ENTRYPOINT ["java", "-jar", "app.jar"]
