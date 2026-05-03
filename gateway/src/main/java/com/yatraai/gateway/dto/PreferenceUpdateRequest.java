package com.yatraai.gateway.dto;

import lombok.Data;

import java.util.List;

@Data
public class PreferenceUpdateRequest {
    private Boolean isVegetarian;
    private List<String> cuisineTags;
    private String travelStyle;
    private String budgetTier;
    private List<String> interestTags;
    private String languagePref;
    private Boolean allowAiSuggestions;
}
