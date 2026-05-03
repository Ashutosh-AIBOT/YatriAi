package com.yatraai.gateway.service;

import com.yatraai.gateway.dto.PreferenceUpdateRequest;
import com.yatraai.gateway.dto.UserDTO;
import com.yatraai.gateway.exception.ApiException;
import com.yatraai.gateway.model.User;
import com.yatraai.gateway.model.UserPreference;
import com.yatraai.gateway.repository.UserPreferenceRepository;
import com.yatraai.gateway.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.OffsetDateTime;
import java.util.UUID;

@Service
@RequiredArgsConstructor
public class UserService {
    private final UserRepository userRepository;
    private final UserPreferenceRepository userPreferenceRepository;

    @Transactional(readOnly = true)
    public UserDTO getProfile(String userId) {
        User user = userRepository.findById(UUID.fromString(userId))
                .orElseThrow(() -> new ApiException(HttpStatus.NOT_FOUND, "User not found"));
        return UserDTO.builder()
                .id(user.getId())
                .name(user.getName())
                .email(user.getEmail())
                .language(user.getLanguage())
                .isActive(user.getIsActive())
                .createdAt(user.getCreatedAt())
                .build();
    }

    @Transactional
    public void updatePreferences(String userId, PreferenceUpdateRequest request) {
        UserPreference pref = userPreferenceRepository.findById(UUID.fromString(userId))
                .orElseThrow(() -> new ApiException(HttpStatus.NOT_FOUND, "Preferences not found"));
        
        if (request.getIsVegetarian() != null) pref.setIsVegetarian(request.getIsVegetarian());
        if (request.getCuisineTags() != null) pref.setCuisineTags(request.getCuisineTags());
        if (request.getTravelStyle() != null) pref.setTravelStyle(request.getTravelStyle());
        if (request.getBudgetTier() != null) pref.setBudgetTier(request.getBudgetTier());
        if (request.getInterestTags() != null) pref.setInterestTags(request.getInterestTags());
        if (request.getLanguagePref() != null) pref.setLanguagePref(request.getLanguagePref());
        if (request.getAllowAiSuggestions() != null) pref.setAllowAiSuggestions(request.getAllowAiSuggestions());

        userPreferenceRepository.save(pref);
    }

    @Transactional
    public void softDelete(String userId) {
        User user = userRepository.findById(UUID.fromString(userId))
                .orElseThrow(() -> new ApiException(HttpStatus.NOT_FOUND, "User not found"));
        user.setDeletedAt(OffsetDateTime.now());
        user.setIsActive(false);
        userRepository.save(user);
    }
}
