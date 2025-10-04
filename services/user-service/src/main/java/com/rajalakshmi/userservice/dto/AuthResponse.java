package com.rajalakshmi.userservice.dto;


public class AuthResponse {
    private String token;

    // --- Constructors ---
    public AuthResponse() {
    }

    public AuthResponse(String token) {
        this.token = token;
    }

    // --- Getter and Setter ---
    public String getToken() {
        return token;
    }

    public void setToken(String token) {
        this.token = token;
    }
}
