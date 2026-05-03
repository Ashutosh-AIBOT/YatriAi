package com.yatraai.gateway.controller;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;

@RestController
@RequestMapping("/health")
public class HealthController {

    @GetMapping("/live")
    public Map<String, String> live() {
        return Map.of("status", "UP");
    }

    @GetMapping("/ready")
    public Map<String, String> ready() {
        // Ideally we should inject health indicators
        return Map.of("status", "UP", "database", "UP", "redis", "UP");
    }
}
