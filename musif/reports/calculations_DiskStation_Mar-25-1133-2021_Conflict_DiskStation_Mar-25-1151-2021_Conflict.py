import numpy as np
import pandas as pd

##################################################################################################
# This function transforms the interval into absolute values, adding the ascending and descending#
##################################################################################################


def make_intervals_absolute(intervals_info):
    intervals_info_columns = intervals_info.columns
    columns_to_merge = [
        iname for iname in intervals_info_columns if '-' in iname]
    new_columns = [iname.replace('-', '') for iname in columns_to_merge]
    intervals_info_abs = pd.DataFrame()
    intervals_info_abs = pd.concat(
        [intervals_info, intervals_info_abs], axis=1)
    for i, c in enumerate(new_columns):
        column_deprecated = intervals_info_abs[columns_to_merge[i]].tolist()
        x = np.nan_to_num(column_deprecated)
        if c in intervals_info_abs:
            y = np.nan_to_num(intervals_info_abs[c])
            intervals_info_abs[c] = list(np.add(x, y))
        else:
            intervals_info_abs[c] = list(x)
        intervals_info_abs = intervals_info_abs.drop(
            columns_to_merge[i], axis=1)
    return intervals_info_abs

    ########################################################################
# Function to generate the files 4xEmphasised_scale_degrees.xlsx
########################################################################


def emphasised_scale_degrees(data, sorting_list, name, results_path, sorting_lists, visualiser_lock, groups=None, additional_info=[]):
    try:
        workbook = openpyxl.Workbook()
        all_columns = data.columns.tolist()
        general_cols = copy.deepcopy(not_used_cols)
        for row in rows_groups:
            if len(rows_groups[row][0]) == 0:
                general_cols.append(row)
            else:
                general_cols += rows_groups[row][0]

        # nombres de todos los intervalos
        third_columns_names_origin = list(set(all_columns) - set(general_cols))
        third_columns_names_origin = sort(
            third_columns_names_origin, sorting_list)
        third_columns_names = ['Total analysed'] + third_columns_names_origin
        third_columns_names2 = ['Total analysed'] + \
            ['1', '4', '5', '7', 'Others']

        # esta hoja va de sumar, así que en todas las columnas el cómputo que hay que hacer es sumar!
        computations = ["sum"]*len(third_columns_names)
        computations2 = ["sum"]*len(third_columns_names2)

        emphdegrees = pd.DataFrame(prepare_data_emphasised_scale_degrees_second(
            data, third_columns_names, third_columns_names2))
        data2 = pd.concat(
            [data[[gc for gc in general_cols if gc in all_columns]], emphdegrees], axis=1)
        _, unique_columns = np.unique(data2.columns, return_index=True)
        data2 = data2.iloc[:, unique_columns]
        hoja_iValues(workbook.create_sheet("Wheighted"), third_columns_names, data, third_columns_names, computations, sorting_lists, groups=groups, last_column=True, last_column_average=False, average=True,
                     columns2=third_columns_names2,  data2=data2, third_columns2=third_columns_names2, computations_columns2=computations2, additional_info=additional_info, ponderate=True)
        hoja_iValues(workbook.create_sheet("Horizontal Per"), third_columns_names, data, third_columns_names, computations, sorting_lists, groups=groups, per=True, average=True, last_column=True, last_column_average=False,
                     columns2=third_columns_names2,  data2=data2, third_columns2=third_columns_names2, computations_columns2=computations2, additional_info=additional_info)
        hoja_iValues(workbook.create_sheet("Vertical Per"), third_columns_names, data, third_columns_names, computations, sorting_lists, groups=groups, per=True, average=False, last_column=True, last_column_average=True,
                     columns2=third_columns_names2,  data2=data2, third_columns2=third_columns_names2, computations_columns2=computations2, additional_info=additional_info)

        # Delete the default sheet
        if "Sheet" in workbook.get_sheet_names():
            std = workbook.get_sheet_by_name('Sheet')
            workbook.remove_sheet(std)
        workbook.save(os.path.join(results_path, name))

        with visualiser_lock:
            subtitile = 'in relation to the global key' if '4a' in name else 'in relation to the local key'
            # VISUALISATIONS
            if groups:
                data_grouped = data.groupby(list(groups))
                for g, datag in data_grouped:
                    result_visualisations = path.join(
                        results_path, 'visualisations', g)
                    if not os.path.exists(result_visualisations):
                        os.mkdir(result_visualisations)

                    name1 = path.join(
                        result_visualisations, '4a.Scale_degrees_GlobalKey.png' if '4a' in name else '4b.scale_degrees_LocalKey.png')
                    customized_plot(
                        name1, data, third_columns_names_origin, subtitile, second_title=g)
            else:
                name1 = path.join(results_path, 'visualisations',
                                  '4a.scale_degrees_GlobalKey.png' if '4a' in name else '4b.scale_degrees_LocalKey.png')
                customized_plot(
                    name1, data, third_columns_names_origin, subtitile)

    except Exception as e:
        logger.error('{}  Problem found:'.format(name), exc_info=True)
