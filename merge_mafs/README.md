#### Usage
Merge ```maf1.txt``` and ```maf2.txt``` to ```maf_combined.txt```

#### Command Line
```
python merge_mafs.py path/to/maf1.txt path/to/maf2.txt path/to/maf_combined.txt
```

### Shell commands to merge two MAFs (Alternative to the above python script)

1. Check if headers are identical

```
grep -v "^#" maf1 | head -1 > header1
grep -v "^#" maf2 | head -1 > header2
diff header1 header2
```

If identical ```diff``` won't return anything

2. Copy MAF1 and give it the new merged MAF filename
```
cp maf1 mergedmaf
```

3. Concatenate MAF2 contents (ignoring comments and header) to the new merged MAF file
```
grep -v -E "^#|^Hugo" maf2 >> mergedmaf
```
