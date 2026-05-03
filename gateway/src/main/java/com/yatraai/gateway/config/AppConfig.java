package com.yatraai.gateway.config;

import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Configuration;

import java.util.List;

@Data
@Configuration
@ConfigurationProperties(prefix = "app")
public class AppConfig {
    private Jwt jwt = new Jwt();
    private RefreshToken refreshToken = new RefreshToken();
    private RateLimit rateLimit = new RateLimit();
    private Cors cors = new Cors();

    @Data
    public static class Jwt {
        private String secret;
        private long expiryMinutes;
    }

    @Data
    public static class RefreshToken {
        private long expiryDays;
    }

    @Data
    public static class RateLimit {
        private long requestsPerMinute;
    }

    @Data
    public static class Cors {
        private List<String> allowedOrigins;
    }
}
