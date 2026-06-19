#!/usr/bin/env python3
"""
Convert Illumina GenomeStudio CSV (GRCh37, Plus strand) to a VCF.
REF/ALT assignment is deferred to bcftools norm after liftover.
Homozygous calls: one allele becomes REF (placeholder), other stays.
Heterozygous calls: allele1=REF placeholder, allele2=ALT.
bcftools norm -f ref.fna will correct the REF/ALT after liftover.
"""
import sys, csv, gzip, re

in_csv   = sys.argv[1]
out_vcf  = sys.argv[2]
sample   = None
records  = {}  # (chr, pos) -> (a1, a2)

SKIP_CHROMS = {"0", "MT", "XY", "M", "Y"}

with open(in_csv) as fh:
    in_data = False
    reader = None
    for line in fh:
        if line.strip() == "[Data]":
            in_data = True
            reader = csv.DictReader(fh)
            for row in reader:
                chrom = row["Chr"].strip()
                if chrom in SKIP_CHROMS:
                    continue
                if sample is None:
                    sample = row["Sample Name"].strip()
                a1 = row["Allele1 - Plus"].strip()
                a2 = row["Allele2 - Plus"].strip()
                # skip no-calls
                if a1 == "-" or a2 == "-" or a1 == "0" or a2 == "0":
                    continue
                pos = int(row["Position"].strip())
                # keep first call per position (duplicates exist)
                key = (chrom, pos)
                if key not in records:
                    records[key] = (a1, a2)
            break

print(f"Read {len(records)} typed variants for sample {sample}", file=sys.stderr)

open_fn = gzip.open if out_vcf.endswith(".gz") else open
with open_fn(out_vcf, "wt") as out:
    out.write("##fileformat=VCFv4.2\n")
    out.write("##reference=GRCh37\n")
    for c in [str(i) for i in range(1,23)] + ["X"]:
        out.write(f"##contig=<ID=chr{c}>\n")
    out.write('##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">\n')
    out.write(f"#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\t{sample}\n")

    for (chrom, pos), (a1, a2) in sorted(records.items(), key=lambda x: (str(x[0][0]).zfill(2), x[0][1])):
        chrom_vcf = f"chr{chrom}"
        if a1 == a2:
            ref, alt, gt = a1, ".", "0/0"
        else:
            ref, alt, gt = a1, a2, "0/1"
        out.write(f"{chrom_vcf}\t{pos}\t.\t{ref}\t{alt}\t.\t.\t.\tGT\t{gt}\n")

print("Done writing VCF", file=sys.stderr)
