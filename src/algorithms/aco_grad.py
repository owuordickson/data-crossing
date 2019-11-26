# -*- coding: utf-8 -*-
"""
@author: "Dickson Owuor"
@credits: "Thomas Runkler, Edmond Menya, and Anne Laurent,"
@license: "MIT"
@version: "1.0"
@email: "owuordickson@gmail.com"
@created: "12 July 2019"

"""
import numpy as np
import random as rand
import matplotlib.pyplot as plt
import pandas
from itertools import cycle, islice
from io import BytesIO
import base64


class GradACO:

    def __init__(self, steps, max_combs, d_set):
        self.steps = steps
        self.max_combs = max_combs
        self.data = d_set
        self.attr_index = self.data.attr_index
        self.e_factor = 0  # evaporation factor
        self.p_matrix = np.ones((self.data.column_size, 3), dtype=int)
        self.valid_bins = []
        self.invalid_bins = []

    def run_ant_colony(self, min_supp):
        all_sols = list()
        win_sols = list()
        loss_sols = list()
        invalid_sols = list()
        for t in range(self.steps):
            for n in range(self.max_combs):
                sol_n = self.generate_rand_pattern()
                # print(sol_n)
                if sol_n and (sol_n not in all_sols):
                    all_sols.append(sol_n)
                    if loss_sols:
                        # check for super-set anti-monotony
                        is_super = GradACO.check_anti_monotony(loss_sols, sol_n, False)
                        is_invalid = GradACO.check_anti_monotony(invalid_sols, sol_n, False)
                        if is_super or is_invalid:
                            continue
                    if win_sols:
                        # check for sub-set anti-monotony
                        is_sub = GradACO.check_anti_monotony(win_sols, sol_n, True)
                        if is_sub:
                            continue
                    supp, sol_gen = self.evaluate_bin_solution(sol_n, min_supp)
                    # print(supp)
                    # print(sol_gen)
                    if supp and (supp >= min_supp) and ([supp, sol_gen] not in win_sols):
                        win_sols.append([supp, sol_gen])
                        self.update_pheromone(sol_gen)
                    elif supp and (supp < min_supp) and ([supp, sol_gen] not in loss_sols):
                        loss_sols.append([supp, sol_gen])
                        # self.update_pheromone(sol_n, False)
                    else:
                        invalid_sols.append([supp, sol_n])
                        # self.update_pheromone(sol_n, False)
        # print("All: "+str(len(all_sols)))
        # print("Winner: "+str(len(win_sols)))
        # print("Losers: "+str(len(loss_sols)))
        # return GradACO.stringfy_pattern(win_sols)
        return win_sols

    def generate_rand_pattern(self):
        p = self.p_matrix
        n = len(self.attr_index)  # self.data.column_size
        pattern = list()
        count = 0
        for i in range(n):
            x = float(rand.randint(1, self.max_combs) / self.max_combs)
            pos = float(p[i][0] / (p[i][0] + p[i][1] + p[i][2]))
            neg = float((p[i][0] + p[i][1]) / (p[i][0] + p[i][1] + p[i][2]))
            if x < pos:
                temp = tuple([self.attr_index[i], '+'])
            elif (x >= pos) and (x < neg):
                temp = tuple([self.attr_index[i], '-'])
            else:
                # temp = tuple([self.data.attr_index[i], 'x'])
                continue
            pattern.append(temp)
            count += 1
        if count <= 1:
            pattern = False
        return pattern

    def evaluate_bin_solution(self, pattern, min_supp):
        # pattern = [('2', '+'), ('4', '+')]
        lst_bin = self.data.lst_bin
        gen_pattern = []
        bin_data = []
        count = 0
        for obj_i in pattern:
            if obj_i in self.invalid_bins:
                continue
            elif obj_i in self.valid_bins:
                # fetch pattern
                for obj in lst_bin:
                    if obj[0] == obj_i:
                        gen_pattern.append(obj[0])
                        bin_data.append([obj[1], obj[2], obj[0]])
                        count += 1
                        break
            else:
                attr_data = False
                for obj in self.data.attr_data:
                    if obj[0] == obj_i[0]:
                        attr_data = obj
                        break
                if attr_data:
                    supp, temp_bin = self.data.get_bin_rank(attr_data, obj_i[1])
                    if supp >= min_supp:
                        self.valid_bins.append(tuple([obj_i[0], '+']))
                        self.valid_bins.append(tuple([obj_i[0], '-']))
                        gen_pattern.append(obj_i)
                        bin_data.append([temp_bin, supp, obj_i])
                        count += 1
                    else:
                        self.invalid_bins.append(tuple([obj_i[0], '+']))
                        self.invalid_bins.append(tuple([obj_i[0], '-']))
                else:
                    # binary does not exist
                    return False
        if count <= 1:
            return False, False
        else:
            supp, new_pattern = GradACO.perform_bin_and(bin_data, self.data.get_size(), min_supp)
            return supp, new_pattern

    def update_pheromone(self, pattern):
        lst_attr = []
        for obj in pattern:
            attr = int(obj[0])
            lst_attr.append(attr)
            symbol = obj[1]
            i = attr - 1
            if symbol == '+':
                self.p_matrix[i][0] += 1
            elif symbol == '-':
                self.p_matrix[i][1] += 1
        for index in self.data.attr_index:
            if int(index) not in lst_attr:
                # print(obj)
                i = int(index) - 1
                self.p_matrix[i][2] += 1

    def plot_pheromone_matrix(self):
        x_plot = np.array(self.p_matrix)
        # print(x_plot)
        # Figure size (width, height) in inches
        # plt.figure(figsize=(4, 4))
        plt.title("+: increasing; -: decreasing; x: irrelevant")
        # plt.xlabel("+: increasing; -: decreasing; x: irrelevant")
        # plt.ylabel('Attribute')
        plt.xlim(0, 3)
        plt.ylim(0, len(self.p_matrix))
        x = [0, 1, 2]
        y = []
        for i in range(len(self.data.title)):
            y.append(i)
            plt.text(-0.3, (i+0.5), self.data.title[i][1][:3])
        plt.xticks(x, [])
        plt.yticks(y, [])
        plt.text(0.5, -0.4, '+')
        plt.text(1.5, -0.4, '-')
        plt.text(2.5, -0.4, 'x')
        plt.pcolor(-x_plot, cmap='gray')
        plt.gray()
        plt.grid()
        plt.show()
        # fig = BytesIO()
        # plt.savefig(fig, format='png')
        # fig.seek(0)  # rewind to beginning of file
        # figdata_png = base64.b64encode(fig.getvalue())
        # return fig

    @staticmethod
    def plot_patterns(list_pattern):
        num = len(list_pattern)
        count = 0
        if num == 1:
            df = pandas.DataFrame(list_pattern[count][0])
            my_colors = list(islice(cycle(['b', 'r', 'g', 'y', 'k']), None, len(df)))
            ax = df.plot(kind='bar', stacked=True, width=1, color=my_colors)
            ax.spines['right'].set_visible(False)
            ax.spines['top'].set_visible(False)
            ax.spines['bottom'].set_position('center')
            plt.ylim(-2, 2)
            plt.xlim(-0.5, len(list_pattern[count][0]))
            plt.yticks([-1, 1], ['-', '+'])
            plt.xticks([], [])
            plt.text(0, 1.8, list_pattern[count][1])
        elif num == 2:
            fig, axes = plt.subplots(2)
            for r in range(2):
                df = pandas.DataFrame(list_pattern[count][0])
                my_colors = list(islice(cycle(['b', 'r', 'g', 'y', 'k']), None, len(df)))
                df.plot(ax=axes[r], kind='bar', stacked=True, width=1, color=my_colors)
                axes[r].spines['right'].set_visible(False)
                axes[r].spines['top'].set_visible(False)
                axes[r].spines['bottom'].set_position('center')
                # axes[r, c].set_title("support: "+str(count))
                axes[r].text(0, 1.8, list_pattern[count][1])
                axes[r].set_xlim([-0.5, len(list_pattern[count][0])])
                axes[r].set_ylim([-2, 2])
                count += 1
            plt.setp(axes, xticks=[], xticklabels=[],
                     yticks=[-1, 1], yticklabels=['-', '+'])
        elif num == 3:
            fig, axes = plt.subplots(2, 2)
            for r in range(2):
                for c in range(2):
                    if count <= 2:
                        df = pandas.DataFrame(list_pattern[count][0])
                        my_colors = list(islice(cycle(['b', 'r', 'g', 'y', 'k']), None, len(df)))
                        df.plot(ax=axes[r, c], kind='bar', stacked=True, width=1, color=my_colors)
                        axes[r, c].spines['right'].set_visible(False)
                        axes[r, c].spines['top'].set_visible(False)
                        axes[r, c].spines['bottom'].set_position('center')
                        # axes[r, c].set_title("support: "+str(count))
                        axes[r, c].text(0, 1.8, list_pattern[count][1])
                        axes[r, c].set_xlim([-0.5, len(list_pattern[count][0])])
                        axes[r, c].set_ylim([-2, 2])
                        count += 1
            plt.setp(axes, xticks=[], xticklabels=[],
                     yticks=[-1, 1], yticklabels=['-', '+'])
        elif num == 4:
            fig, axes = plt.subplots(2, 2)
            for r in range(2):
                for c in range(2):
                    df = pandas.DataFrame(list_pattern[count][0])
                    my_colors = list(islice(cycle(['b', 'r', 'g', 'y', 'k']), None, len(df)))
                    df.plot(ax=axes[r, c], kind='bar', stacked=True, width=1, color=my_colors)
                    axes[r, c].spines['right'].set_visible(False)
                    axes[r, c].spines['top'].set_visible(False)
                    axes[r, c].spines['bottom'].set_position('center')
                    # axes[r, c].set_title("support: "+str(count))
                    axes[r, c].text(0, 1.8, list_pattern[count][1])
                    axes[r, c].set_xlim([-0.5, len(list_pattern[count][0])])
                    axes[r, c].set_ylim([-2, 2])
                    count += 1
            plt.setp(axes, xticks=[], xticklabels=[],
                     yticks=[-1, 1], yticklabels=['-', '+'])
        else:
            plt.title("No Patterns Found")
        # plt.show()
        fig_bytes = BytesIO()
        plt.savefig(fig_bytes, format='png')
        fig_bytes.seek(0)  # rewind to beginning of file
        buffer = b''.join(fig_bytes)
        fig_base64 = base64.b64encode(buffer)
        img_data = fig_base64.decode('utf-8')
        return img_data

    @staticmethod
    def check_anti_monotony(lst_p, p_arr, ck_sub):
        result = False
        if ck_sub:
            for obj in lst_p:
                result = set(p_arr).issubset(set(obj[1]))
                if result:
                    break
        else:
            for obj in lst_p:
                result = set(p_arr).issuperset(set(obj[1]))
                if result:
                    break
        return result

    @staticmethod
    def perform_bin_and(unsorted_bins, n, thd_supp):
        lst_bin = sorted(unsorted_bins, key=lambda x: x[1])
        final_bin = np.array([])
        pattern = []
        count = 0
        for obj in lst_bin:
            temp_bin = final_bin
            if temp_bin.size != 0:
                temp_bin = temp_bin & obj[0]
                supp = float(np.sum(temp_bin)) / float(n * (n - 1.0) / 2.0)
                if supp >= thd_supp:
                    final_bin = temp_bin
                    pattern.append(obj[2])
                    count += 1
            else:
                final_bin = obj[0]
                pattern.append(obj[2])
                count += 1
        supp = float(np.sum(final_bin)) / float(n * (n - 1.0) / 2.0)
        if count >= 2:
            return supp, pattern
        else:
            return 0, unsorted_bins

    # @staticmethod
    # def stringfy_pattern(sols):
    #    sols.sort(key=lambda k: (k[0], k[1]), reverse=True)
    #    list_pat = list()
    #    for obj in sols:
    #        sup = obj[0]
    #        var_pat = list()
    #        for item in obj[1]:
    #            var_pat.append((str(item[0]) + str(item[1])))
    #        list_pat.append(([sup, var_pat]))
    #    return list_pat