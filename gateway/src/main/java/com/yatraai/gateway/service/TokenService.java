package com.yatraai.gateway.service;

import com.yatraai.gateway.config.AppConfig;
import com.yatraai.gateway.exception.ApiException;
import com.yatraai.gateway.model.User;
import io.jsonwebtoken.Claims;
import io.jsonwebtoken.JwtException;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;

import javax.crypto.SecretKey;
import java.nio.charset.StandardCharsets;
import java.util.Date;

@Service
@RequiredArgsConstructor
public class TokenService {
    private final AppConfig appConfig;

    private SecretKey getSigningKey() {
        byte[] keyBytes = appConfig.getJwt().getSecret().getBytes(StandardCharsets.UTF_8);
        return Keys.hmacShaKeyFor(keyBytes);
    }

    public String generateAccessToken(User user) {
        long expirationTimeMillis = appConfig.getJwt().getExpiryMinutes() * 60 * 1000;
        return Jwts.builder()
                .subject(user.getId().toString())
                .claim("email", user.getEmail())
                .issuedAt(new Date())
                .expiration(new Date(System.currentTimeMillis() + expirationTimeMillis))
                .signWith(getSigningKey(), Jwts.SIG.HS256)
                .compact();
    }

    public String validateTokenAndGetUserId(String token) {
        try {
            Claims claims = Jwts.parser()
                    .verifyWith(getSigningKey())
                    .build()
                    .parseSignedClaims(token)
                    .getPayload();
            return claims.getSubject();
        } catch (JwtException | IllegalArgumentException e) {
            throw new ApiException(HttpStatus.UNAUTHORIZED, "Invalid JWT token");
        }
    }
}
