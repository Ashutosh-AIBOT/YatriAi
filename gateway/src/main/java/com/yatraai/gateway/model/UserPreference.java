package com.yatraai.gateway.model;

import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;
import jakarta.persistence.*;
import lombok.*;
import org.hibernate.annotations.UpdateTimestamp;

import java.time.OffsetDateTime;
import java.util.List;
import java.util.UUID;

@Entity
@Table(name = "user_preferences")
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class UserPreference {
    @Id
    @Column(name = "user_id")
    private UUID userId;

    @OneToOne(fetch = FetchType.LAZY)
    @MapsId
    @JoinColumn(name = "user_id")
    private User user;

    @Column(name = "is_vegetarian")
    @Builder.Default
    private Boolean isVegetarian = false;

    @JdbcTypeCode(SqlTypes.ARRAY)
    @Column(name = "cuisine_tags", columnDefinition = "text[]")
    private List<String> cuisineTags;

    @Column(name = "travel_style", length = 50)
    @Builder.Default
    private String travelStyle = "balanced";

    @Column(name = "budget_tier", length = 20)
    @Builder.Default
    private String budgetTier = "medium";

    @JdbcTypeCode(SqlTypes.ARRAY)
    @Column(name = "interest_tags", columnDefinition = "text[]")
    private List<String> interestTags;

    @Column(name = "language_pref", length = 10)
    @Builder.Default
    private String languagePref = "en";

    @Column(name = "allow_ai_suggestions")
    @Builder.Default
    private Boolean allowAiSuggestions = true;

    @UpdateTimestamp
    @Column(name = "updated_at")
    private OffsetDateTime updatedAt;
}
