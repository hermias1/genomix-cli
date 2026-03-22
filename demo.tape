Output demo.gif

Set Shell zsh
Set FontSize 14
Set Width 1200
Set Height 700
Set Theme "Catppuccin Mocha"
Set Padding 20
Set TypingSpeed 50ms

# Setup
Hide
Type "source ~/Desktop/genomix/.venv/bin/activate && export PYTHONPATH=~/Desktop/genomix && cd /tmp/genomix_test"
Enter
Sleep 1s
Show

# Launch genomix
Type "python -m genomix.cli"
Enter
Sleep 8s

# Show help
Type "/help"
Enter
Sleep 3s

# Ask about a VCF file
Type "Read brca_variants.vcf and give me a clinical summary of all variants"
Enter
Sleep 20s

# Follow-up question
Type "Which of these variants are most concerning for cancer risk?"
Enter
Sleep 15s

# Exit
Type "/quit"
Enter
Sleep 1s
