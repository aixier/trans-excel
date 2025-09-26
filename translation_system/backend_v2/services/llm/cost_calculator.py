"""Cost calculation optimization for various LLM providers."""

import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
import json


logger = logging.getLogger(__name__)


@dataclass
class ModelPricing:
    """Pricing information for a specific model."""
    model_name: str
    provider: str
    input_cost_per_1k: Decimal  # Cost per 1K input tokens
    output_cost_per_1k: Decimal  # Cost per 1K output tokens
    currency: str = "USD"
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class CostCalculation:
    """Result of a cost calculation."""
    input_tokens: int
    output_tokens: int
    total_tokens: int
    input_cost_usd: Decimal
    output_cost_usd: Decimal
    total_cost_usd: Decimal
    total_cost_cny: Decimal
    exchange_rate: Decimal
    model: str
    provider: str
    calculation_time: datetime = field(default_factory=datetime.now)


class CostCalculator:
    """Advanced cost calculator for LLM API usage."""

    def __init__(self, exchange_rate_usd_to_cny: float = 7.3):
        """
        Initialize CostCalculator.

        Args:
            exchange_rate_usd_to_cny: USD to CNY exchange rate
        """
        self.exchange_rate = Decimal(str(exchange_rate_usd_to_cny))
        self.logger = logging.getLogger(self.__class__.__name__)

        # Initialize pricing data
        self.pricing_data: Dict[str, ModelPricing] = {}
        self._load_default_pricing()

        # Cost tracking
        self.session_costs: Dict[str, List[CostCalculation]] = {}
        self.total_cost_usd = Decimal('0')
        self.total_cost_cny = Decimal('0')

        self.logger.info(f"CostCalculator initialized with exchange rate: {self.exchange_rate} CNY/USD")

    def _load_default_pricing(self):
        """Load default pricing data for major providers."""

        # OpenAI pricing (as of 2024)
        self.add_model_pricing(
            "gpt-4-turbo", "openai",
            input_cost=0.01, output_cost=0.03
        )
        self.add_model_pricing(
            "gpt-4", "openai",
            input_cost=0.03, output_cost=0.06
        )
        self.add_model_pricing(
            "gpt-3.5-turbo", "openai",
            input_cost=0.001, output_cost=0.002
        )

        # Anthropic Claude pricing
        self.add_model_pricing(
            "claude-3-opus", "anthropic",
            input_cost=0.015, output_cost=0.075
        )
        self.add_model_pricing(
            "claude-3-sonnet", "anthropic",
            input_cost=0.003, output_cost=0.015
        )
        self.add_model_pricing(
            "claude-3-haiku", "anthropic",
            input_cost=0.00025, output_cost=0.00125
        )

        # Google Gemini pricing (estimated)
        self.add_model_pricing(
            "gemini-pro", "google",
            input_cost=0.0005, output_cost=0.0015
        )

        # Azure OpenAI (similar to OpenAI)
        self.add_model_pricing(
            "gpt-4-azure", "azure",
            input_cost=0.03, output_cost=0.06
        )
        self.add_model_pricing(
            "gpt-35-turbo-azure", "azure",
            input_cost=0.001, output_cost=0.002
        )

        # Domestic providers (estimated)
        self.add_model_pricing(
            "qwen-max", "alibaba",
            input_cost=0.008, output_cost=0.016
        )
        self.add_model_pricing(
            "baichuan2", "baichuan",
            input_cost=0.006, output_cost=0.012
        )
        self.add_model_pricing(
            "chatglm3", "zhipu",
            input_cost=0.005, output_cost=0.010
        )

    def add_model_pricing(
        self,
        model_name: str,
        provider: str,
        input_cost: float,
        output_cost: float,
        currency: str = "USD"
    ):
        """
        Add or update pricing for a model.

        Args:
            model_name: Name of the model
            provider: Provider name
            input_cost: Cost per 1K input tokens
            output_cost: Cost per 1K output tokens
            currency: Currency code
        """
        pricing = ModelPricing(
            model_name=model_name,
            provider=provider,
            input_cost_per_1k=Decimal(str(input_cost)),
            output_cost_per_1k=Decimal(str(output_cost)),
            currency=currency
        )

        key = f"{provider}:{model_name}"
        self.pricing_data[key] = pricing

        self.logger.debug(f"Added pricing for {key}: ${input_cost}/{output_cost} per 1K tokens")

    def calculate_cost(
        self,
        input_tokens: int,
        output_tokens: int,
        model: str,
        provider: str
    ) -> CostCalculation:
        """
        Calculate cost for token usage.

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            model: Model name
            provider: Provider name

        Returns:
            Cost calculation result
        """
        try:
            # Get pricing data
            pricing = self._get_model_pricing(model, provider)

            if not pricing:
                # Use fallback pricing if model not found
                self.logger.warning(f"No pricing data for {provider}:{model}, using fallback")
                pricing = self._get_fallback_pricing(provider)

            # Calculate costs
            input_cost_usd = (
                Decimal(str(input_tokens)) * pricing.input_cost_per_1k / Decimal('1000')
            ).quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP)

            output_cost_usd = (
                Decimal(str(output_tokens)) * pricing.output_cost_per_1k / Decimal('1000')
            ).quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP)

            total_cost_usd = input_cost_usd + output_cost_usd

            # Convert to CNY
            total_cost_cny = (total_cost_usd * self.exchange_rate).quantize(
                Decimal('0.01'), rounding=ROUND_HALF_UP
            )

            calculation = CostCalculation(
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=input_tokens + output_tokens,
                input_cost_usd=input_cost_usd,
                output_cost_usd=output_cost_usd,
                total_cost_usd=total_cost_usd,
                total_cost_cny=total_cost_cny,
                exchange_rate=self.exchange_rate,
                model=model,
                provider=provider
            )

            # Update totals
            self.total_cost_usd += total_cost_usd
            self.total_cost_cny += total_cost_cny

            self.logger.debug(
                f"Cost calculated for {provider}:{model}: "
                f"${total_cost_usd:.6f} (¥{total_cost_cny:.2f}) "
                f"for {input_tokens + output_tokens} tokens"
            )

            return calculation

        except Exception as e:
            self.logger.error(f"Failed to calculate cost: {e}")
            # Return zero cost calculation
            return CostCalculation(
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=input_tokens + output_tokens,
                input_cost_usd=Decimal('0'),
                output_cost_usd=Decimal('0'),
                total_cost_usd=Decimal('0'),
                total_cost_cny=Decimal('0'),
                exchange_rate=self.exchange_rate,
                model=model,
                provider=provider
            )

    def _get_model_pricing(self, model: str, provider: str) -> Optional[ModelPricing]:
        """Get pricing for a specific model."""
        key = f"{provider}:{model}"
        return self.pricing_data.get(key)

    def _get_fallback_pricing(self, provider: str) -> ModelPricing:
        """Get fallback pricing based on provider."""
        fallback_pricing = {
            "openai": ModelPricing("unknown", "openai", Decimal('0.01'), Decimal('0.03')),
            "anthropic": ModelPricing("unknown", "anthropic", Decimal('0.008'), Decimal('0.024')),
            "google": ModelPricing("unknown", "google", Decimal('0.001'), Decimal('0.002')),
            "azure": ModelPricing("unknown", "azure", Decimal('0.01'), Decimal('0.03')),
            "alibaba": ModelPricing("unknown", "alibaba", Decimal('0.008'), Decimal('0.016')),
            "baichuan": ModelPricing("unknown", "baichuan", Decimal('0.006'), Decimal('0.012')),
            "zhipu": ModelPricing("unknown", "zhipu", Decimal('0.005'), Decimal('0.010'))
        }

        return fallback_pricing.get(
            provider,
            ModelPricing("unknown", "unknown", Decimal('0.005'), Decimal('0.015'))
        )

    def track_session_cost(self, session_id: str, calculation: CostCalculation):
        """Track cost for a specific session."""
        if session_id not in self.session_costs:
            self.session_costs[session_id] = []

        self.session_costs[session_id].append(calculation)

    def get_session_cost_summary(self, session_id: str) -> Dict[str, Any]:
        """Get cost summary for a session."""
        if session_id not in self.session_costs:
            return {
                'session_id': session_id,
                'total_cost_usd': '0.00',
                'total_cost_cny': '0.00',
                'total_tokens': 0,
                'request_count': 0,
                'by_model': {},
                'by_provider': {}
            }

        calculations = self.session_costs[session_id]

        # Aggregate totals
        total_cost_usd = sum(c.total_cost_usd for c in calculations)
        total_cost_cny = sum(c.total_cost_cny for c in calculations)
        total_tokens = sum(c.total_tokens for c in calculations)

        # Group by model
        by_model = {}
        by_provider = {}

        for calc in calculations:
            # By model
            model_key = f"{calc.provider}:{calc.model}"
            if model_key not in by_model:
                by_model[model_key] = {
                    'cost_usd': Decimal('0'),
                    'cost_cny': Decimal('0'),
                    'tokens': 0,
                    'requests': 0
                }

            by_model[model_key]['cost_usd'] += calc.total_cost_usd
            by_model[model_key]['cost_cny'] += calc.total_cost_cny
            by_model[model_key]['tokens'] += calc.total_tokens
            by_model[model_key]['requests'] += 1

            # By provider
            if calc.provider not in by_provider:
                by_provider[calc.provider] = {
                    'cost_usd': Decimal('0'),
                    'cost_cny': Decimal('0'),
                    'tokens': 0,
                    'requests': 0
                }

            by_provider[calc.provider]['cost_usd'] += calc.total_cost_usd
            by_provider[calc.provider]['cost_cny'] += calc.total_cost_cny
            by_provider[calc.provider]['tokens'] += calc.total_tokens
            by_provider[calc.provider]['requests'] += 1

        # Convert Decimal to string for JSON serialization
        for model_data in by_model.values():
            model_data['cost_usd'] = str(model_data['cost_usd'])
            model_data['cost_cny'] = str(model_data['cost_cny'])

        for provider_data in by_provider.values():
            provider_data['cost_usd'] = str(provider_data['cost_usd'])
            provider_data['cost_cny'] = str(provider_data['cost_cny'])

        return {
            'session_id': session_id,
            'total_cost_usd': str(total_cost_usd),
            'total_cost_cny': str(total_cost_cny),
            'total_tokens': total_tokens,
            'request_count': len(calculations),
            'by_model': by_model,
            'by_provider': by_provider,
            'exchange_rate': str(self.exchange_rate)
        }

    def estimate_batch_cost(
        self,
        texts: List[str],
        model: str,
        provider: str,
        avg_tokens_per_char: float = 0.3,
        output_ratio: float = 1.2
    ) -> Dict[str, Any]:
        """
        Estimate cost for a batch of texts.

        Args:
            texts: List of texts to translate
            model: Model name
            provider: Provider name
            avg_tokens_per_char: Average tokens per character
            output_ratio: Output tokens ratio to input

        Returns:
            Cost estimation
        """
        try:
            # Estimate token counts
            total_chars = sum(len(text) for text in texts)
            estimated_input_tokens = int(total_chars * avg_tokens_per_char)
            estimated_output_tokens = int(estimated_input_tokens * output_ratio)

            # Calculate cost
            calculation = self.calculate_cost(
                estimated_input_tokens,
                estimated_output_tokens,
                model,
                provider
            )

            return {
                'text_count': len(texts),
                'total_characters': total_chars,
                'estimated_input_tokens': estimated_input_tokens,
                'estimated_output_tokens': estimated_output_tokens,
                'estimated_cost_usd': str(calculation.total_cost_usd),
                'estimated_cost_cny': str(calculation.total_cost_cny),
                'cost_per_text_usd': str(calculation.total_cost_usd / len(texts)),
                'cost_per_text_cny': str(calculation.total_cost_cny / len(texts)),
                'model': model,
                'provider': provider
            }

        except Exception as e:
            self.logger.error(f"Failed to estimate batch cost: {e}")
            return {
                'error': str(e),
                'text_count': len(texts),
                'estimated_cost_usd': '0.00',
                'estimated_cost_cny': '0.00'
            }

    def update_exchange_rate(self, new_rate: float):
        """Update USD to CNY exchange rate."""
        old_rate = self.exchange_rate
        self.exchange_rate = Decimal(str(new_rate))

        self.logger.info(f"Exchange rate updated: {old_rate} -> {self.exchange_rate} CNY/USD")

    def get_pricing_info(self) -> Dict[str, Any]:
        """Get current pricing information for all models."""
        pricing_info = {}

        for key, pricing in self.pricing_data.items():
            pricing_info[key] = {
                'model': pricing.model_name,
                'provider': pricing.provider,
                'input_cost_per_1k': str(pricing.input_cost_per_1k),
                'output_cost_per_1k': str(pricing.output_cost_per_1k),
                'currency': pricing.currency,
                'last_updated': pricing.last_updated.isoformat()
            }

        return {
            'models': pricing_info,
            'exchange_rate': str(self.exchange_rate),
            'total_cost_usd': str(self.total_cost_usd),
            'total_cost_cny': str(self.total_cost_cny)
        }

    def export_cost_data(self, session_id: str = None) -> List[Dict[str, Any]]:
        """Export cost data for analysis."""
        cost_data = []

        if session_id:
            calculations = self.session_costs.get(session_id, [])
        else:
            calculations = []
            for session_calculations in self.session_costs.values():
                calculations.extend(session_calculations)

        for calc in calculations:
            cost_data.append({
                'calculation_time': calc.calculation_time.isoformat(),
                'model': calc.model,
                'provider': calc.provider,
                'input_tokens': calc.input_tokens,
                'output_tokens': calc.output_tokens,
                'total_tokens': calc.total_tokens,
                'input_cost_usd': str(calc.input_cost_usd),
                'output_cost_usd': str(calc.output_cost_usd),
                'total_cost_usd': str(calc.total_cost_usd),
                'total_cost_cny': str(calc.total_cost_cny),
                'exchange_rate': str(calc.exchange_rate)
            })

        return cost_data


# Global cost calculator instance
cost_calculator = CostCalculator()