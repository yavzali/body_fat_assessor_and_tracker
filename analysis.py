"""AI analysis service.

Orchestrates AI-powered body composition analysis using OpenAI or Anthropic.
"""

import base64
import json
import time
from typing import Optional

import httpx
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic

from config import settings, ErrorMessages, AnalysisPrompts
from schemas import AIAnalysisResult
from models import ConfidenceLevel, PhotoQuality


class AIAnalysisError(Exception):
    """Exception raised for AI analysis errors."""
    pass


class AnalysisService:
    """Service for AI-powered body composition analysis."""
    
    def __init__(self):
        """Initialize AI clients based on configuration."""
        self.provider = settings.ai_provider
        
        if self.provider == "openai":
            if not settings.openai_api_key:
                raise ValueError("OpenAI API key not configured")
            self.openai_client = AsyncOpenAI(api_key=settings.openai_api_key)
        
        elif self.provider == "anthropic":
            if not settings.anthropic_api_key:
                raise ValueError("Anthropic API key not configured")
            self.anthropic_client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        
        else:
            raise ValueError(f"Unsupported AI provider: {self.provider}")
    
    async def analyze_body_composition(
        self,
        image_data: bytes,
        prompt: Optional[str] = None,
    ) -> tuple[AIAnalysisResult, int]:
        """Analyze body composition from image.
        
        Args:
            image_data: Image bytes
            prompt: Optional custom prompt (uses default if not provided)
            
        Returns:
            Tuple of (analysis_result, processing_time_ms)
            
        Raises:
            AIAnalysisError: If analysis fails
        """
        start_time = time.time()
        
        try:
            if self.provider == "openai":
                result = await self._analyze_with_openai(image_data, prompt)
            else:  # anthropic
                result = await self._analyze_with_anthropic(image_data, prompt)
            
            processing_time = int((time.time() - start_time) * 1000)
            return result, processing_time
            
        except Exception as e:
            raise AIAnalysisError(f"{ErrorMessages.AI_ANALYSIS_FAILED}: {str(e)}")
    
    async def _analyze_with_openai(
        self,
        image_data: bytes,
        prompt: Optional[str] = None,
    ) -> AIAnalysisResult:
        """Analyze using OpenAI GPT-4 Vision.
        
        Args:
            image_data: Image bytes
            prompt: Optional custom prompt
            
        Returns:
            Analysis result
        """
        try:
            # Encode image to base64
            base64_image = base64.b64encode(image_data).decode('utf-8')
            
            # Prepare messages
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt or AnalysisPrompts.BASE_PROMPT,
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}",
                            },
                        },
                    ],
                }
            ]
            
            # Call OpenAI API
            response = await self.openai_client.chat.completions.create(
                model=settings.openai_model,
                messages=messages,
                max_tokens=settings.ai_max_tokens,
                temperature=settings.ai_temperature,
            )
            
            # Extract and parse response
            content = response.choices[0].message.content
            return self._parse_ai_response(content)
            
        except Exception as e:
            raise AIAnalysisError(f"OpenAI analysis failed: {str(e)}")
    
    async def _analyze_with_anthropic(
        self,
        image_data: bytes,
        prompt: Optional[str] = None,
    ) -> AIAnalysisResult:
        """Analyze using Anthropic Claude.
        
        Args:
            image_data: Image bytes
            prompt: Optional custom prompt
            
        Returns:
            Analysis result
        """
        try:
            # Encode image to base64
            base64_image = base64.b64encode(image_data).decode('utf-8')
            
            # Prepare messages
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": base64_image,
                            },
                        },
                        {
                            "type": "text",
                            "text": prompt or AnalysisPrompts.BASE_PROMPT,
                        },
                    ],
                }
            ]
            
            # Call Anthropic API
            response = await self.anthropic_client.messages.create(
                model=settings.anthropic_model,
                max_tokens=settings.ai_max_tokens,
                temperature=settings.ai_temperature,
                messages=messages,
            )
            
            # Extract and parse response
            content = response.content[0].text
            return self._parse_ai_response(content)
            
        except Exception as e:
            raise AIAnalysisError(f"Anthropic analysis failed: {str(e)}")
    
    def _parse_ai_response(self, response_text: str) -> AIAnalysisResult:
        """Parse AI response into structured format.
        
        Args:
            response_text: Raw text response from AI
            
        Returns:
            Parsed and validated analysis result
            
        Raises:
            AIAnalysisError: If parsing fails
        """
        try:
            # Clean up response (remove markdown code blocks if present)
            cleaned = response_text.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()
            
            # Parse JSON
            data = json.loads(cleaned)
            
            # Validate and create schema
            result = AIAnalysisResult(
                body_fat_percentage=float(data["body_fat_percentage"]),
                confidence=ConfidenceLevel(data["confidence"].lower()),
                reasoning=data["reasoning"],
                photo_quality=PhotoQuality(data["photo_quality"].lower()),
            )
            
            return result
            
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            # If structured parsing fails, try to extract key information
            raise AIAnalysisError(
                f"Failed to parse AI response. Raw response: {response_text[:200]}"
            )
    
    async def analyze_multi_angle(
        self,
        front_image: bytes,
        side_image: Optional[bytes] = None,
        back_image: Optional[bytes] = None,
    ) -> tuple[AIAnalysisResult, int]:
        """Analyze body composition from multiple angles (Phase 2).
        
        Args:
            front_image: Front view image bytes
            side_image: Optional side view image bytes
            back_image: Optional back view image bytes
            
        Returns:
            Tuple of (analysis_result, processing_time_ms)
        """
        # For Phase 2 - placeholder for now
        # Will implement multi-image analysis
        return await self.analyze_body_composition(front_image)
    
    def validate_analysis_result(self, result: AIAnalysisResult) -> bool:
        """Validate that analysis result is reasonable.
        
        Args:
            result: Analysis result to validate
            
        Returns:
            True if valid, False otherwise
        """
        # Check body fat percentage is in reasonable range
        if not 5.0 <= result.body_fat_percentage <= 50.0:
            return False
        
        # Check that reasoning is substantive
        if len(result.reasoning) < 20:
            return False
        
        return True
