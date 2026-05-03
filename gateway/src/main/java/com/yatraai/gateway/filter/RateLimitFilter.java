package com.yatraai.gateway.filter;

import com.yatraai.gateway.config.AppConfig;
import com.yatraai.gateway.exception.ApiResponse;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.github.bucket4j.Bandwidth;
import io.github.bucket4j.Bucket;
import io.github.bucket4j.BucketConfiguration;
import io.github.bucket4j.Refill;
import io.github.bucket4j.redis.lettuce.cas.LettuceBasedProxyManager;
import io.lettuce.core.RedisClient;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.slf4j.MDC;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.annotation.Order;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;
import java.time.Duration;

@Component
@Order(3)
public class RateLimitFilter extends OncePerRequestFilter {

    private final AppConfig appConfig;
    private final ObjectMapper objectMapper;
    private final LettuceBasedProxyManager<byte[]> proxyManager;

    public RateLimitFilter(AppConfig appConfig, ObjectMapper objectMapper, @Value("${spring.data.redis.url}") String redisUrl) {
        this.appConfig = appConfig;
        this.objectMapper = objectMapper;
        RedisClient redisClient = RedisClient.create(redisUrl);
        this.proxyManager = LettuceBasedProxyManager.builderFor(redisClient)
                .withExpirationStrategy(io.github.bucket4j.distributed.ExpirationAfterWriteStrategy.basedOnTimeForRefillingBucketUpToMax(Duration.ofMinutes(1)))
                .build();
    }

    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain filterChain) throws ServletException, IOException {
        String ip = request.getRemoteAddr();
        String userId = request.getUserPrincipal() != null ? request.getUserPrincipal().getName() : ip;

        Bucket bucket = proxyManager.builder().build(userId.getBytes(), this::getConfig);

        if (bucket.tryConsume(1)) {
            filterChain.doFilter(request, response);
        } else {
            response.setStatus(HttpStatus.TOO_MANY_REQUESTS.value());
            response.setContentType("application/json");
            ApiResponse<Void> apiResponse = ApiResponse.error(429, "Too many requests", MDC.get("traceId"));
            response.getWriter().write(objectMapper.writeValueAsString(apiResponse));
        }
    }

    private BucketConfiguration getConfig() {
        long requests = appConfig.getRateLimit().getRequestsPerMinute();
        Bandwidth limit = Bandwidth.classic(requests, Refill.greedy(requests, Duration.ofMinutes(1)));
        return BucketConfiguration.builder().addLimit(limit).build();
    }
}
