#!/bin/bash
# This script will locate line 36 and fix the syntax error

# Save the original file with a backup
cp /app/hybrid_search.py /app/hybrid_search.py.bak

# Get the contents of line 36 to see what's wrong
LINE=$(sed -n '36p' /app/hybrid_search.py)
echo "Original line: $LINE"

# Look for a pattern like "timeout=X, url" and fix it 
# by moving the timeout to the end
if [[ $LINE == *"timeout="* ]]; then
  # Extract the timeout value
  TIMEOUT=$(echo $LINE | grep -o "timeout=[0-9]*")
  
  # Remove the timeout from the line
  FIXED_LINE=$(echo $LINE | sed "s/$TIMEOUT, //")
  
  # Add the timeout at the end before the closing parenthesis
  FIXED_LINE=$(echo $FIXED_LINE | sed "s/)/, $TIMEOUT)/")
  
  # Replace the line in the file
  sed -i "36s/.*/$FIXED_LINE/" /app/hybrid_search.py
  
  echo "Fixed line: $FIXED_LINE"
else
  echo "Could not identify the pattern to fix"
  # Show a larger context
  sed -n '30,42p' /app/hybrid_search.py
fi

# Verify syntax with Python
python -c "import hybrid_search" 2>/dev/null
if [ $? -eq 0 ]; then
  echo "Syntax is now valid!"
else
  echo "Syntax is still invalid"
  python -c "import hybrid_search" 2>&1
fi
