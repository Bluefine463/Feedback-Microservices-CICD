package com.rajalakshmi.apigateway.config;

import org.springframework.cloud.gateway.route.RouteLocator;
import org.springframework.cloud.gateway.route.builder.RouteLocatorBuilder;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class GatewayConfig {


    @Bean
    public RouteLocator routes(RouteLocatorBuilder builder) {
        return builder.routes()
                .route("user-service", r -> r.path("/users/**")
                        .uri("https://build383build383-user-service.azurewebsites.net"))
                .route("feedback-service", r -> r.path("/feedback/**")
                        .uri("https://build383build383-feedback-service.azurewebsites.net"))
                .build();
    }
}
