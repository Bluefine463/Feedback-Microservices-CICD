FROM eclipse-temurin:17-jre-alpine
WORKDIR /app
COPY target/*.jar app.jar
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "app.jar"]
## disable step 1 when running in pipeline since pipeline does the mvn clean package on
##its own to decrease time usage.
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
