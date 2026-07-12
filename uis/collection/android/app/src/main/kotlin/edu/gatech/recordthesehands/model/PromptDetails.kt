package edu.gatech.recordthesehands.model

/**
 * Data class representing a prompt to be shown to the user.
 *
 * @param id Unique identifier for the prompt
 * @param text The text to display (e.g., the word or phrase to sign)
 * @param videoResId Resource ID for the video demonstration, or null if no video is available
 */
data class PromptDetails(
    val id: String,
    val text: String,
    val videoResId: Int? = null
)
