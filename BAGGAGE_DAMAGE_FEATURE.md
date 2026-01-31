# Baggage Damage Refund Eligibility Feature

## Overview

The Baggage Damage Refund Eligibility checker is a vision-based AI compliance tool that analyzes photos of damaged checked hard-shell suitcases to determine if they qualify for airline refunds according to policy.

## Features Implemented

### Backend

- **Endpoint**: `POST /api/compliance/baggage/damage-refund/check`
- **File**: `backend/app/api/routes_compliance.py`
- **Logic**: `backend/app/rag/compliance_checker.py` → `check_baggage_damage_refund_eligibility()`
- **Policy Document**: `backend/sample_docs/airline_checked_baggage_damage_refund_policy_v1.txt`

**Capabilities:**

- Multi-provider vision model support (OpenAI GPT-4V, Anthropic Claude 3.5 Sonnet, Ollama LLaVA)
- Structured damage assessment (type, severity 0-3, functional impact)
- Policy rule application (reporting window, eligible damage matching, exclusions)
- Confidence scoring and detailed rationale
- Recommended next steps for claimants

### Frontend

- **Page**: Compliance Page with "Baggage Damage Claims" tab
- **Component**: `frontend/src/components/BaggageDamageChecker.jsx`
- **API Client**: `frontend/src/api/client.js` → `checkBaggageDamageEligibility()`

**UI Features:**

- Drag-and-drop image upload with preview
- Optional reporting time input (hours since pickup/delivery)
- Vision provider selection (uses ModelPicker state)
- Real-time analysis with loading state
- Structured results display:
  - Decision badge (Eligible/Not Eligible/Needs Review) with confidence
  - Damage assessment breakdown
  - Policy application details
  - Cited policy references
  - Recommended next steps

## How to Use

### 1. Start the Application

```bash
# Use the Node.js launcher (recommended)
node start-dev.js

# Or use the batch file
start.bat
```

### 2. Navigate to Compliance Page

- Open your browser to `http://localhost:5176` (or whatever port the frontend uses)
- Log in if required
- Click on "Compliance" in the navigation menu
- Switch to the "Baggage Damage Claims" tab

### 3. Upload and Analyze

1. **Select Provider**: Choose your vision model provider from the dropdown (top-right)
   - OpenAI (GPT-4V) - Recommended for accuracy
   - Anthropic (Claude 3.5 Sonnet) - Good alternative
   - Ollama (LLaVA) - Local model option

2. **Upload Image**: Click the upload area or drag-and-drop a photo of your damaged suitcase
   - Supported formats: PNG, JPG, GIF, WEBP
   - Max size: 10MB
   - Best results: Clear, well-lit photos showing damage

3. **Optional Timing**: Enter how many hours ago the damage was reported (if applicable)
   - Policy requires reporting within 24 hours of baggage pickup/delivery
   - Leave empty if unknown

4. **Check Eligibility**: Click the "Check Eligibility" button

5. **Review Results**: The AI will provide:
   - **Decision**: Eligible, Not Eligible, or Needs Review
   - **Confidence**: Percentage certainty (0-100%)
   - **Damage Assessment**: Types observed (cracks, holes, broken wheels), severity level, functional impact
   - **Policy Application**: Whether reporting window was met, if damage matches eligible criteria, any exclusion triggers
   - **Policy References**: Exact quotes from the policy document
   - **Next Steps**: Recommended actions for the claimant

## Testing Tips

### Sample Test Cases

**Eligible Damage Examples:**

- Large cracks in hard shell (severity 2-3)
- Holes or punctures exposing contents (severity 3)
- Broken retractable handles (severity 2)
- Detached or broken wheels (severity 2-3)
- Deep gouges with sharp edges (severity 2)

**Not Eligible Examples:**

- Minor cosmetic scuffs (severity 0-1)
- Light scratches without functional impact (severity 0)
- Pre-existing wear and tear (exclusion)
- Normal airline handling marks (exclusion)
- Overpacking-related damage (exclusion)

**Needs Review Cases:**

- Ambiguous damage severity (borderline severity 1-2)
- Multiple damage types with mixed eligibility
- Missing reporting time information
- Poor photo quality preventing assessment
- Unclear if damage is pre-existing

### Example Test Images

You can test with various damaged suitcase images. Good test images should show:

- Clear view of the damage
- Context (full suitcase or clear section)
- Good lighting
- Sharp focus

## API Response Schema

```json
{
  "decision": "eligible | not_eligible | needs_review",
  "confidence": 0.85,
  "damage_assessment": {
    "observed_damage_types": ["crack", "broken_wheel"],
    "severity": 2,
    "functional_impairment": "moderate",
    "notes": "Large vertical crack on right side panel..."
  },
  "policy_application": {
    "reporting_window_met": true,
    "eligible_damage_match": true,
    "exclusion_triggers": [],
    "policy_references": [
      {
        "section": "Section 4.1 - Eligible Damage",
        "quote": "Cracks longer than 3 inches that compromise structural integrity"
      }
    ]
  },
  "rationale": "The observed damage (large crack with sharp edges)...",
  "next_steps": [
    "File a formal claim with the airline within 7 days",
    "Include this photo plus additional angles showing full suitcase",
    "Retain original baggage claim ticket and flight boarding pass"
  ],
  "needs_more_info": false
}
```

## Technical Details

### Vision Model Integration

- Images are base64-encoded and sent to vision APIs
- Temperature set to 0 for deterministic compliance decisions
- Strict JSON schema enforcement in prompts
- Field validation with sensible defaults

### Performance

- Policy file caching (loaded once, reused for all requests)
- File size validation (10MB limit)
- Image type validation (JPEG, PNG, GIF, WEBP)
- Response times: 3-10 seconds depending on provider

### Security

- File size limits prevent abuse
- Image validation prevents non-image uploads
- Provider validation ensures only supported models used
- Logging of all eligibility checks for audit trail

## Troubleshooting

**"Failed to analyze image"**

- Check that the vision provider is properly configured
- Ensure API keys are set in `.env` file
- Verify image is a valid format and under 10MB
- Try a different provider

**Backend not running**

- Run `node start-dev.js` to start servers
- Check `http://localhost:8001/docs` for API documentation
- Verify `backend/.env` file has required keys

**Frontend build errors**

- Run `npm install` in frontend directory
- Check Node.js version (should be 16+)
- Clear `node_modules` and reinstall if needed

## Next Steps / Future Enhancements

- [ ] Add multiple image upload support (different angles)
- [ ] Implement claim history tracking
- [ ] Add PDF report generation for claims
- [ ] Support for soft-shell luggage (different policy)
- [ ] Integration with airline claim submission APIs
- [ ] Add damage severity visualization (heatmap overlay)
- [ ] Multi-language policy support

## Files Modified/Created

**Backend:**

- ✅ `backend/app/rag/compliance_checker.py` - Added `check_baggage_damage_refund_eligibility()` method
- ✅ `backend/app/api/routes_compliance.py` - Added `/baggage/damage-refund/check` endpoint
- ✅ `backend/sample_docs/airline_checked_baggage_damage_refund_policy_v1.txt` - Policy document

**Frontend:**

- ✅ `frontend/src/components/BaggageDamageChecker.jsx` - New component
- ✅ `frontend/src/pages/CompliancePage.jsx` - Added tab navigation and integration
- ✅ `frontend/src/api/client.js` - Added `checkBaggageDamageEligibility()` function

**Documentation:**

- ✅ This file (`BAGGAGE_DAMAGE_FEATURE.md`)
