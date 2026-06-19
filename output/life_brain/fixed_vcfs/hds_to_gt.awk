BEGIN { OFS="\t" }
/^##FORMAT=<ID=HDS/ {
    print "##FORMAT=<ID=GT,Number=1,Type=String,Description=\"Phased Genotype\">"
    next
}
/^#/ { print; next }
{
    if ($9 == "HDS") {
        $9 = "GT"
        for (i = 10; i <= NF; i++) {
            n = split($i, hds, ",")
            if (n >= 2) {
                gt1 = (hds[1]+0 >= 0.5) ? 1 : 0
                gt2 = (hds[2]+0 >= 0.5) ? 1 : 0
                $i = gt1 "|" gt2
            } else {
                $i = "./."
            }
        }
    }
    print
}
