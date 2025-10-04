#FROM maven:3.9.6-eclipse-temurin-17 AS build
#WORKDIR /app
#COPY pom.xml .
#COPY src ./src
#RUN mvn clean package -DskipTests


#run-time only dockerfile
#compile in azure-pipeline ( incl a task there to compile parallely)


FROM eclipse-temurin:17-jre-alpine
WORKDIR /app
COPY target/*.jar app.jar
EXPOSE 8081
ENTRYPOINT ["java", "-jar", "app.jar"]
