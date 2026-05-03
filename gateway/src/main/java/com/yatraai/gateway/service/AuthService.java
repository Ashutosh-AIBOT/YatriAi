package com.yatraai.gateway.service;

import com.yatraai.gateway.config.AppConfig;
import com.yatraai.gateway.dto.LoginRequest;
import com.yatraai.gateway.dto.RegisterRequest;
import com.yatraai.gateway.exception.ApiException;
import com.yatraai.gateway.model.RefreshToken;
import com.yatraai.gateway.model.User;
import com.yatraai.gateway.model.UserPreference;
import com.yatraai.gateway.repository.RefreshTokenRepository;
import com.yatraai.gateway.repository.UserPreferenceRepository;
import com.yatraai.gateway.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.OffsetDateTime;
import java.util.Map;
import java.util.UUID;

@Service
@RequiredArgsConstructor
public class AuthService {
    private final UserRepository userRepository;
    private final UserPreferenceRepository userPreferenceRepository;
    private final RefreshTokenRepository refreshTokenRepository;
    private final TokenService tokenService;
    private final PasswordEncoder passwordEncoder;
    private final AppConfig appConfig;

    @Transactional
    public Map<String, Object> register(RegisterRequest request) {
        if (userRepository.findByEmail(request.getEmail()).isPresent()) {
            throw new ApiException(HttpStatus.BAD_REQUEST, "Email already exists");
        }

        User user = User.builder()
                .name(request.getName())
                .email(request.getEmail())
                .passwordHash(passwordEncoder.encode(request.getPassword()))
                .build();
        userRepository.save(user);

        UserPreference preference = UserPreference.builder()
                .user(user)
                .build();
        userPreferenceRepository.save(preference);

        return Map.of("userId", user.getId());
    }

    @Transactional
    public Map<String, String> login(LoginRequest request) {
        User user = userRepository.findByEmailAndDeletedAtIsNull(request.getEmail())
                .orElseThrow(() -> new ApiException(HttpStatus.UNAUTHORIZED, "Invalid credentials"));

        if (!passwordEncoder.matches(request.getPassword(), user.getPasswordHash())) {
            throw new ApiException(HttpStatus.UNAUTHORIZED, "Invalid credentials");
        }

        String accessToken = tokenService.generateAccessToken(user);
        String refreshTokenString = UUID.randomUUID().toString(); // simple implementation for token hash

        RefreshToken refreshToken = RefreshToken.builder()
                .user(user)
                .tokenHash(passwordEncoder.encode(refreshTokenString)) // hash before saving
                .expiresAt(OffsetDateTime.now().plusDays(appConfig.getRefreshToken().getExpiryDays()))
                .build();
        refreshTokenRepository.save(refreshToken);

        return Map.of(
                "accessToken", accessToken,
                "refreshToken", refreshTokenString
        );
    }
}
