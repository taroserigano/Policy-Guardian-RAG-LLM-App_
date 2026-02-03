# Model Comparison Guide

## How to Compare Fine-Tuned vs Base Model

I've created comparison tools to measure the improvements from fine-tuning!

### Quick Test (1 question, ~30 seconds)

**Option 1: Command Line**
```bash
cd backend
python quick_compare.py
```

**Option 2: Windows Batch File**
```bash
cd backend
run_comparison.bat
```

This will ask **one policy question** to both models side-by-side:
- **Base Model**: llama3.1:8b (before fine-tuning)
- **Fine-Tuned Model**: policy-compliance-llm (after fine-tuning)

### Full Comparison Test (10 questions, ~10 minutes)

```bash
cd backend
python compare_models.py
```

This comprehensive test:
- ✅ Runs 10 policy questions covering all documents
- ✅ Scores accuracy based on keyword detection
- ✅ Measures response time
- ✅ Shows side-by-side comparisons
- ✅ Generates detailed JSON report
- ✅ Provides improvement statistics

### Test Questions Covered

1. **Leave Policy** (4 questions)
   - Vacation days (20 days expected)
   - Sick leave (10 days expected)
   - Maternity leave (16 weeks expected)
   
2. **Remote Work** (3 questions)
   - Hybrid days allowed (2 days/week)
   - Full remote requirements (3+ days needs approval)
   - Equipment stipend ($500 + $75/month)

3. **Data Privacy** (2 questions)
   - Retention period (7 years)
   - Encryption standards (AES-256, TLS 1.2+)

4. **NDA** (2 questions)
   - Confidentiality duration (5 years)
   - What's confidential (trade secrets, technical, business)

### Expected Improvements

Your fine-tuned model should show:

✅ **Better Accuracy** - More correct facts and numbers
- "20 vacation days" vs vague "standard vacation"
- "10 sick days" vs generic "paid sick leave"
- "$500 equipment stipend" vs "equipment provided"

✅ **More Specific** - References exact policy details
- "16 weeks maternity (8 paid, 8 unpaid)" vs "extended leave"
- "7 years retention" vs "legally required period"

✅ **Policy Language** - Uses terminology from training
- "Department head approval" vs "management approval"
- "Confidentiality obligation" vs "keep things secret"

### Understanding the Results

The test scores each answer by detecting key information:

**Example:**
```
Question: "How many vacation days do employees get?"
Keywords: ["20", "annual", "days", "year"]

Base Model Score: 1/4 keywords (only mentioned "days")
Fine-Tuned Score: 4/4 keywords (mentioned all)

✅ Improvement: +3 keywords
```

### Sample Output

```
================================================================================
Test #1: How many vacation days do employees get per year?
Expected: Should mention 20 days of paid annual leave
================================================================================

Base Model (llama3.1:8b):
  Time: 2.3s
  Score: 1/4 keywords found
  Found: days
  Answer: Employees typically receive paid vacation time based on company 
  policy and length of service. The exact number varies...

Fine-Tuned Model (policy-compliance-llm):
  Time: 2.1s  
  Score: 4/4 keywords found
  Found: 20, annual, days, year
  Answer: According to the Employee Leave Policy, full-time employees receive 
  20 days of paid annual leave per year. This accrues at a rate of 1.67 days 
  per month...

✅ Fine-tuned model is MORE accurate (+3 keywords)
```

### Final Summary Shows

- **Total Accuracy**: Fine-tuned vs Base (e.g., 85% vs 45%)
- **Improvement**: Keyword boost percentage
- **Speed**: Average response times
- **Win/Tie/Loss**: Question breakdown
- **Overall Assessment**: Success rating

### Manual Testing

You can also test manually in terminal:

```bash
# Base model
ollama run llama3.1:8b "How many vacation days do employees get?"

# Fine-tuned model  
ollama run policy-compliance-llm "How many vacation days do employees get?"
```

Compare the answers yourself!

### What Makes a Good Result?

🎉 **Excellent** (>70% accuracy improvement)
- Fine-tuned model gets most facts right
- Includes specific numbers and details
- Uses policy-specific language

✅ **Good** (40-70% improvement)
- Fine-tuned model more accurate than base
- Gets key facts correct
- Some policy terminology

⚠️ **Needs Work** (<40% improvement)
- Minimal difference between models
- Consider: more training data, more epochs, better data quality

### Troubleshooting

**"Model not found" error:**
```bash
# Check available models
ollama list

# Pull base model if missing
ollama pull llama3.1:8b

# Re-import fine-tuned model if missing
cd backend/finetune_llm
ollama create policy-compliance-llm -f Modelfile
```

**"Connection refused" error:**
- Make sure Ollama is running
- Check: `http://localhost:11434` in browser

**Slow responses:**
- Normal for 8B models on CPU
- Each question takes 10-30 seconds
- Full test takes ~10 minutes total

### Interpreting Results

If fine-tuning worked well, you should see:
- 50-80% more accurate on policy questions
- Specific numbers instead of vague answers
- Policy terminology from your training data
- Confident, structured responses

If results are underwhelming:
- Check training data quality
- Consider training more epochs (you did 3)
- Verify model imported correctly
- Test with more diverse questions

---

**Ready to test?**

Start with: `python quick_compare.py` (30 seconds)
Then run: `python compare_models.py` (full analysis)
