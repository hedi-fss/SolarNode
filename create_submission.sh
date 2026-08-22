#!/bin/bash
# Create submission package for IEEE ComSoc competition

echo "Creating submission package..."
mkdir -p submission

# Copy report
cp report/solarnode_report_final.pdf submission/

# Copy figures
cp -r figures submission/

# Copy source code
cp -r app/ frontend/ config.py run.py requirements.txt submission/source/

# Copy documentation
cp SUBMISSION_CHECKLIST.md submission/
cp video_script.txt submission/

# Create zip
zip -r solarnode_submission.zip submission/

echo "✅ Submission package created: solarnode_submission.zip"
echo ""
echo "Contents:"
ls -la submission/
