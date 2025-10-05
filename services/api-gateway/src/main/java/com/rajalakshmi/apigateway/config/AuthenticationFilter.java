package com.rajalakshmi.apigateway.config;

import io.jsonwebtoken.Claims;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.cloud.context.config.annotation.RefreshScope;
import org.springframework.cloud.gateway.filter.GatewayFilter;
import org.springframework.cloud.gateway.filter.GatewayFilterChain;
import org.springframework.http.HttpStatus;
import org.springframework.http.server.reactive.ServerHttpRequest;
import org.springframework.http.server.reactive.ServerHttpResponse;
import org.springframework.stereotype.Component;
import org.springframework.web.server.ServerWebExchange;
import reactor.core.publisher.Mono;

import java.security.Key;
import java.util.List;

@RefreshScope
@Component
public class AuthenticationFilter implements GatewayFilter {

    @Value("${jwt.secret}")
    private String secret;

    @Override
    public Mono<Void> filter(ServerWebExchange exchange, GatewayFilterChain chain) {
        ServerHttpRequest request = exchange.getRequest();

        final List<String> apiEndpoints = List.of("/users/register", "/users/login");

        if (apiEndpoints.stream().anyMatch(uri -> request.getURI().getPath().contains(uri))) {
            return chain.filter(exchange);
        }

        if (!request.getHeaders().containsKey("Authorization")) {
            return this.onError(exchange, HttpStatus.UNAUTHORIZED);
        }

        final String authHeader = request.getHeaders().getOrEmpty("Authorization").get(0);
        if (authHeader == null || !authHeader.startsWith("Bearer ")) {
            return this.onError(exchange, HttpStatus.UNAUTHORIZED);
        }

        final String token = authHeader.substring(7);

        try {
            byte[] keyBytes = secret.getBytes();
            Key key = Keys.hmacShaKeyFor(keyBytes);
            Claims claims = Jwts.parserBuilder().setSigningKey(key).build().parseClaimsJws(token).getBody();

            String userId = claims.get("id", String.class);
            String userRole = claims.get("role", String.class);

            exchange.getRequest().mutate()
                    .header("X-User-Id", userId)
                    .header("X-User-Role", userRole)
                    .build();

        } catch (Exception e) {
            return this.onError(exchange, HttpStatus.UNAUTHORIZED);
        }

        return chain.filter(exchange);
    }

    private Mono<Void> onError(ServerWebExchange exchange, HttpStatus httpStatus) {
        ServerHttpResponse response = exchange.getResponse();
        response.setStatusCode(httpStatus);
        return response.setComplete();
    }
}
