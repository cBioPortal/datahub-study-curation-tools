import csv
import os
import sys
import argparse


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--sample-map", required=True, help="Path to the sample ID map .csv", type=str)
    parser.add_argument("--sample-from", required=True, help='"from ID" field in sample-map file', type=str)
    parser.add_argument("--sample-to", required=True, help='"to ID" field in sample-map file', type=str)

    parser.add_argument("-p", "--patient-map", required=True, help="Path to the patient ID map .csv", type=str)
    parser.add_argument("--patient-from", required=True, help='"from ID" field in patient-map file', type=str)
    parser.add_argument("--patient-to", required=True, help='"to ID" field in patient-map file', type=str)

    parser.add_argument("-path", "--source-path", required=True, help="Path to the study directory", type=str)
    parser.add_argument("-dest", "--dest-path", required=True, help="Path to the destination directory", type=str)

    parser.add_argument("--drop-unknown", help="Not to fail on IDs not found in the map", type=bool, default=False)

    args = parser.parse_args()
    print(args)

    smap = load_map(args.sample_map, args.sample_from, args.sample_to)
    pmap = load_map(args.patient_map, args.patient_from, args.patient_to)

    rewrite_study(args.source_path, args.dest_path, patient_map=pmap, sample_map=smap, strict=not args.drop_unknown)
    print("done")


def load_map(map_fname, from_f, to_f):
    with open(map_fname) as f:
        map_list = list(csv.DictReader(f))

    # TODO strict check that values are unique
    return {map_dict[from_f]: map_dict[to_f] for map_dict in map_list if map_dict[to_f]}


def rewrite_study(study_dir, output_dir, patient_map, sample_map, strict=True):

    for fname in [fname for fname in os.listdir(study_dir) if "data" in fname]:
        header = extract_header(study_dir + "/" + fname)

        by_column = lambda **maps_kv: multi_map(
            study_dir, fname, {header.index(field): map for field, map in maps_kv.items()}, output_dir, strict=strict
        )

        if "patient_id" in header and "sample_id" not in header:
            by_column(patient_id=patient_map)

        elif "patient_id" in header and "sample_id" in header:
            by_column(patient_id=patient_map, sample_id=sample_map)

        elif "sample_id" in header:
            by_column(sample_id=sample_map)

        elif "sampleid" in header:
            by_column(sampleid=sample_map)

        elif "tumor_sample_barcode" in header:
            # if "matched_norm_sample_barcode" in header:
            #     # TBD - map two columns.
            #     tumor_sample_barcode - with set strictness
            #     and
            #     matched_norm_sample_barcode - with no strictness?

            by_column(tumor_sample_barcode=sample_map)

        elif "id" in header and "chrom" in header:
            raise Exception("Not implemented for id/chrom file type {}".format(fname))
            # by_column("id", sample_map)

        elif ("hugo_symbol" in header or "entrez_gene_id" in header) and "tumor_sample_barcode" not in header:
            index_cols = find_sample_position(fname, header)
            map_matrix_type(study_dir, fname, sample_map, output_dir, index_cols)

        elif "composite.element.ref" in header:
            raise Exception("Not implemented for composite.element.ref file type {}".format(fname))
            # index_cols = find_sample_position(fname, header)
            # map_matrix_type(study_dir, fname, sample_map, output_dir, index_cols)

        elif "entity_stable_id" in header:
            raise Exception("Not implemented for entity_stable_id file type {}".format(fname))
            # index_cols = find_sample_position(fname, header)
            # map_generic_assay(fname, sample_ids_list, output_dir, index_cols)

        else:
            raise Exception("File {} of unknown type".format(fname))

    try:
        os.mkdir(output_dir + "/case_lists")
    except FileExistsError:
        pass

    for cl_fname in os.listdir(study_dir + "/case_lists"):
        map_case_list(study_dir + "/case_lists", cl_fname, sample_map, output_dir + "/case_lists", strict=strict)


def extract_header(filename, lower=True, split=True):
    with open(filename, "r") as infile:
        for line in infile:
            if line.startswith("#"):
                continue
            else:
                if lower:
                    line = line.lower()
                line = line.rstrip("\n")
                if split:
                    line = line.split("\t")
                return line
            break


class StrictModeNoMappingFound(Exception):
    pass


def _multi_map_one_line(line, column_index_to_map_dict, strict):
    values = line.rstrip("\n").split("\t")

    for idx, map in column_index_to_map_dict.items():

        current_id = values[idx]
        try:
            new_id = map[current_id]
        except KeyError:
            msg = "No mapping found for {}".format(current_id)
            if strict:
                raise StrictModeNoMappingFound(msg)
            else:
                print(msg)
                return ""  # because we don't want half-mapped entries

        values[idx] = new_id

    return "\t".join(values) + "\n"


def multi_map(study_dir, fname, column_index_to_map_dict, output_dir, strict=True):

    header_data = ""
    data = ""
    print("Processing file " + fname + " ")

    fullheader = False

    with open(study_dir + "/" + fname, "r") as data_file:
        for lnum, line in enumerate(data_file, 1):

            if line.startswith("#"):  # processing "preamble"
                header_data += line

            elif not fullheader:  # first line after "preamble" is the header
                header_data += line
                fullheader = True

            else:  # now processing data lines
                try:
                    data += _multi_map_one_line(line, column_index_to_map_dict, strict=strict)
                except StrictModeNoMappingFound as e:
                    msg = "{} from {}:{}".format(e, fname, lnum)
                    if strict:
                        raise StrictModeNoMappingFound(msg)
                    else:
                        print(msg)
                        continue

    if data != "":
        print("Writing remapped data to " + output_dir + "/" + fname)
        with open(output_dir + "/" + fname, "w") as outfile:
            outfile.write(header_data)
            outfile.write(data)
    else:
        print("Empty remmaped file " + fname + " - skipping..")


def map_matrix_type(study_dir, fname, sample_map, output_dir, index_cols):
    print("Processing matrix file " + fname + "...")

    data_cols = []
    header_cols = extract_header(study_dir + "/" + fname, lower=False)
    header = "\t".join(header_cols)

    for ind, value in enumerate(header_cols):
        if value in sample_map:
            data_cols.append(ind)

    if not data_cols:  # TODO check strict?
        print("No data cols detected?")
        return None

    data = ""
    with open(study_dir + "/" + fname, "r") as data_file:

        for lnum, line in enumerate(data_file, 1):

            if line.startswith("#"):
                data += line

            elif line.startswith(header):  # .startswith because of possible trailing '\n' mismatch

                mapped_header_line = [header_cols[i] for i in index_cols]

                # TODO strict?
                # Actual mapping now:
                mapped_header_line += [sample_map[header_cols[i]] for i in data_cols]

                data += "\t".join(mapped_header_line) + "\n"

            else:

                line = line.strip("\n").split("\t")

                filtered_data_line = [line[i] for i in index_cols + data_cols]

                ## TODO FIXME What was this for?
                # if "" in filtered_data_line and len(filtered_data_line) == 2:
                #     continue

                data += "\t".join(filtered_data_line) + "\n"

    if data != "":
        print("Writing remapped data to " + output_dir + "/" + fname + "\n")
        with open(output_dir + "/" + fname, "w") as datafile:
            datafile.write(data.strip("\n"))
    else:
        print("Sample IDs to subset are not present in {}. Skipping..".format(fname))


def _remap_list_of_ids(ids, id_map, init_offset=0, strict=True):
    res = []
    offset = init_offset
    for current_id in ids:
        try:
            res.append(id_map[current_id])
        except KeyError:
            msg = "No mapping found for {!r} columns {}-{}".format(current_id, offset, offset + len(current_id))
            if strict:
                raise StrictModeNoMappingFound(msg)
            else:
                print(msg)
                continue

        offset += len(current_id) + 1  # 1 is for the delimiter
    return res


def _unique_keep_order(list):
    res = []
    s = set()
    for i in list:
        if i not in s:
            s.add(i)
            res.append(i)
    return res


def map_case_list(dir, fname, id_map, output_dir, strict=True):
    data = ""
    with open(dir + "/" + fname) as f:
        for lnum, line in enumerate(f, 1):
            if line.startswith("case_list_ids: "):

                orig_ids = line.split(" ", 1)[1].rstrip("\n").rstrip("\t").split("\t")

                try:
                    new_ids = _remap_list_of_ids(orig_ids, id_map, init_offset=len("case_list_ids: "), strict=strict)
                except StrictModeNoMappingFound as e:
                    raise StrictModeNoMappingFound("{} from {}:{}".format(e, fname, lnum))

                data += "case_list_ids: " + "\t".join(_unique_keep_order(new_ids)) + "\n"
            else:
                data += line

    if data != "":
        print("Writing remapped data to " + output_dir + "/" + fname)
        with open(output_dir + "/" + fname, "w") as outfile:
            outfile.write(data)
    else:
        print("Empty remmaped file " + fname + " - skipping..")


def find_sample_position(file, header):
    HEADER_KEYWORDS = [
        "composite.element.ref",
        "hugo_symbol",
        "entrez_gene_id",
        "entity_stable_id",
        "name",
        "description",
        "url",
        "confidence_statement",
    ]
    index_cols = []
    for keyword in header:
        if keyword in HEADER_KEYWORDS:
            index_cols.append(header.index(keyword))
    return index_cols


if __name__ == "__main__":
    main()
