
class Levenshtein():
    def __init__(self, del_cost, ins_cost, sub_cost):
        self.del_cost = del_cost
        self.ins_cost = ins_cost
        self.sub_cost = sub_cost

    def distance(self, needle, haystack, limit):
        # del_cost = penalty for not typing part of the text (user is just lazy)
        # ins_cost = penalty for typing something thats not in the text
        # sub_cost = penalty for typing something wrong
        len_haystack = len(haystack)
        len_needle = len(needle)
        current_row = [0]*(len_haystack+1)
        previous_row = [0]*(len_haystack+1)
        for j in range(len_haystack):
            deletion = current_row[j] + self.del_cost
            current_row[j+1] = deletion
        #print(current_row)
        min_j = 0
        max_j = len_haystack
        for i, c in enumerate(needle):

            if i & 1:
                current_row[0] = previous_row[0]+self.ins_cost
                row_min = None
                for j in range(min_j, max_j):
                    d = haystack[j]
                    deletion = current_row[j] + self.del_cost
                    insertion = previous_row[j + 1] + self.ins_cost
                    substitution = previous_row[j] + (c != d)*self.sub_cost
                    mn = min(insertion, deletion, substitution)
                    current_row[j+1] = mn
                    ex = len_haystack-j-len_needle+i
                    if ex < 0: mn += ex*-self.ins_cost
                    if ex > 0: mn += ex*self.del_cost
                    if row_min is None or mn < row_min:
                        row_min = mn
                #print(current_row)
                if row_min is not None and row_min > limit:
                    return None
            else:
                previous_row[0] = current_row[0]+self.ins_cost
                row_min = None
                for j in range(min_j, max_j):
                    d = haystack[j]
                    deletion = previous_row[j] + self.del_cost
                    insertion = current_row[j + 1] + self.ins_cost
                    substitution = current_row[j] + (c != d)*self.sub_cost
                    mn = min(insertion, deletion, substitution)
                    previous_row[j+1] = mn
                    ex = len_haystack-j-len_needle+i
                    if ex < 0: mn += ex*-self.ins_cost
                    if ex > 0: mn += ex*self.del_cost
                    if row_min is None or mn < row_min:
                        row_min = mn
                #print(previous_row)
                if row_min is not None and row_min > limit:
                    return None


        if len_needle & 1:
            if previous_row[-1] > limit:
                return None
            return previous_row[-1]
        else:
            if current_row[-1] > limit:
                return None
            return current_row[-1]
