
def compute_expected_loss(
    subject_premium: float,
    expected_loss_ratio: float,
) -> float:
    """Compute expected loss to the layer."""
    return subject_premium * expected_loss_ratio


def compute_indicated_rate(
    expected_loss: float,
    subject_premium: float,
) -> float:
    """Compute indicated rate as expected loss / subject premium."""
    return expected_loss / subject_premium


def compute_indicated_premium(
    expected_loss: float,
) -> float:
    """Compute indicated premium (before expense and profit loading)."""
    return expected_loss


def price_cat_xol(
    limit: float,
    attachment: float,
    subject_premium: float,
    expected_loss_ratio: float,
) -> dict:
    """
    Price a property cat XOL layer.

    Parameters
    ----------
    limit : float
        Reinsurance limit (coverage amount).
    attachment : float
        Attachment point (retention).
    subject_premium : float
        Cedent's subject premium.
    expected_loss_ratio : float
        Expected loss ratio to the layer (as a decimal, e.g., 0.08 for 8%).

    Returns
    -------
    dict
        Pricing results including expected loss, rate, and premium.
    """
    expected_loss = compute_expected_loss(subject_premium, expected_loss_ratio)
    indicated_rate = compute_indicated_rate(expected_loss, subject_premium)
    indicated_premium = compute_indicated_premium(expected_loss)

    return {
        "limit": limit,
        "attachment": attachment,
        "subject_premium": subject_premium,
        "expected_loss_ratio": expected_loss_ratio,
        "expected_loss": expected_loss,
        "indicated_rate": indicated_rate,
        "indicated_premium": indicated_premium,
    }


def display_results(results: dict) -> None:
    """Print pricing results in a readable format."""
    limit_m = results["limit"] / 1e6
    attachment_m = results["attachment"] / 1e6

    print("=" * 50)
    print(f"  Cat XOL Pricing: {limit_m:.0f}M xs {attachment_m:.0f}M")
    print("=" * 50)
    print(f"  Subject Premium:      ${results['subject_premium']:>14,.0f}")
    print(f"  Expected Loss Ratio:  {results['expected_loss_ratio']:>14.1%}")
    print(f"  Expected Loss:        ${results['expected_loss']:>14,.0f}")
    print(f"  Indicated Rate:       {results['indicated_rate']:>14.3%}")
    print(f"  Indicated Premium:    ${results['indicated_premium']:>14,.0f}")
    print("=" * 50)



results_1 = price_cat_xol(
    limit=10_000_000,
    attachment=5_000_000,
    subject_premium=50_000_000,
    expected_loss_ratio=0.08,
)

results_2 = price_cat_xol(
    limit=15_000_000,
    attachment=15_000_000,
    subject_premium=50_000_000,
    expected_loss_ratio=0.04,
)

display_results(results_1)
print()
display_results(results_2)

#print(f"Treaty: {results['limit'] / 1e6:.0f}M xs {results['attachment'] / 1e6:.0f}M")
#print(f"Subject Premium: ${results['subject_premium']:,.0f}")
#print(f"Expected Loss Ratio: {results['expected_loss_ratio']:.1%}")
#print(f"Expected Loss: ${results['expected_loss']:,.0f}")
#print(f"Indicated Rate: {results['indicated_rate']:.3%}")
#print(f"Indicated Premium: ${results['indicated_premium']:,.0f}")