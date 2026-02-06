import streamlit as st
import re
import subprocess
import pandas as pd
import tempfile
import os

def is_valid_dna(sequence):
    """Checks if a string is a valid DNA sequence."""
    return bool(re.match("^[ATCG]+$", sequence, re.IGNORECASE))

def run_blast(program, database, query_sequence):
    """Runs a BLAST search and returns stdout and stderr."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".fasta") as temp_fasta:
        temp_fasta.write(f">query\n{query_sequence}")
        temp_fasta_path = temp_fasta.name

    try:
        # Using -outfmt 6 for tabular output
        command = [
            program,
            "-query", temp_fasta_path,
            "-db", database,
            "-outfmt", "6 qseqid sseqid pident length mismatch gapopen qstart qend sstart send evalue bitscore"
        ]
        
        process = subprocess.run(command, capture_output=True, text=True, check=True)
        return process.stdout, process.stderr
    except subprocess.CalledProcessError as e:
        return "", e.stderr
    finally:
        os.remove(temp_fasta_path)

def parse_blast_output(blast_output):
    """Parses tabular BLAST output into a Pandas DataFrame."""
    if not blast_output.strip():
        return pd.DataFrame()

    column_names = [
        "qseqid", "sseqid", "pident", "length", "mismatch", "gapopen",
        "qstart", "qend", "sstart", "send", "evalue", "bitscore"
    ]
    
    # Use io.StringIO to treat the string as a file for pandas
    from io import StringIO
    df = pd.read_csv(StringIO(blast_output), sep='\t', names=column_names)
    return df

st.title("Streamlit BLAST App")

st.header("DNA Sequence Validator")
sequence = st.text_area("Enter DNA sequence for validation:")

if sequence:
    if is_valid_dna(sequence):
        st.success("The sequence is a valid DNA sequence.")
    else:
        st.error("The sequence contains invalid characters. Only A, T, C, and G are allowed.")

st.header("BLAST Search")

blast_program = st.selectbox("Select BLAST Program", ["blastn", "blastp", "blastx"])
blast_database = st.text_input("Enter BLAST Database Name or Path (e.g., 'nt', 'nr', or 'dummy_db')")
blast_sequence = st.text_area("Enter sequence for BLAST search:")
run_blast_button = st.button("Run BLAST")

if run_blast_button:
    if blast_sequence and blast_database:
        st.info(f"Running {blast_program} against {blast_database}...")
        stdout, stderr = run_blast(blast_program, blast_database, blast_sequence)

        if stdout:
            st.subheader("BLAST Results")
            blast_df = parse_blast_output(stdout)
            if not blast_df.empty:
                st.dataframe(blast_df)
            else:
                st.warning("No BLAST hits found.")
        
        if stderr:
            st.error(f"BLAST Error: {stderr}")
            st.warning("Please ensure the selected BLAST program, database, and query sequence are valid.")
    else:
        st.warning("Please enter both a query sequence and a database name/path to run BLAST.")

