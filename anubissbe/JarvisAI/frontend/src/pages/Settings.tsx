// ... existing code ...

<TextField
  select
  fullWidth
  label="AI Model"
  value={model}
  onChange={(e) => setModel(e.target.value)}
>
  <MenuItem value="llama3">Llama 3</MenuItem>
  <MenuItem value="mistral">Mistral</MenuItem>
  <MenuItem value="gemma:7b">Gemma 7B</MenuItem>
  <MenuItem value="phi3:mini">Phi-3 Mini</MenuItem>
  <MenuItem value="llama3:8b">Llama 3 8B</MenuItem>
  <MenuItem value="llama3:70b">Llama 3 70B</MenuItem>
</TextField>

// ... existing code ...