#! usr/bin/perl
use strict;
use warnings;

# script to separate nagative entrez id rows to a new file and remove the cytoband column if exists from CNA table

my $file = $ARGV[0];
my $neg_ids = $ARGV[1];


open(FH,"<$file") or die();
open(NF,">$neg_ids") or die();
my $header_line = <FH>;
my @header_values = split("\t",$header_line);

my $i =0; my $cyto_col = -1; my $entrez_col;
foreach(@header_values)
{	
	if($_ eq "Cytoband")
	{
		$cyto_col = $i;
	}
	if($_ eq "Entrez_Gene_Id")
	{
		$entrez_col = $i;
	}
	$i++;
}

if($cyto_col != -1)
{
	splice(@header_values,$cyto_col,1);
}
my $final_header = join("\t",@header_values);

my $pos_data = "";
my $neg_data = "";
while(<FH>)
{
	chomp($_);
	my @ar = split("\t",$_);
	if($ar[$entrez_col] < 0 && $cyto_col != -1)
	{
		splice(@ar,$cyto_col,1);
		$neg_data .= join("\t",@ar);
		$neg_data .= "\n";
	}
	elsif($ar[$entrez_col] < 0 && $cyto_col == -1)
	{
		$neg_data .= join("\t",@ar);
		$neg_data .= "\n";
	}
	elsif($ar[$entrez_col] >= 0 && $cyto_col != -1)
	{
		splice(@ar,$cyto_col,1);
		$pos_data .= join("\t",@ar);
		$pos_data .= "\n";
	}
	else
	{
		$pos_data .= join("\t",@ar);
		$pos_data .= "\n";
	}

}
print NF $final_header.$neg_data;

unlink $file;

open(PF, ">$file") or die();
print PF $final_header.$pos_data;
