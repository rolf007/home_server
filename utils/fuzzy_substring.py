
class Levenshtein():
    def __init__(self, del_cost, ins_cost, sub_cost):
        self.del_cost = del_cost
        self.ins_cost = ins_cost
        self.sub_cost = sub_cost

    def distance(self, needle, haystack):
        # del_cost = penalty for not typing part of the text (user is just lazy)
        # ins_cost = penalty for typing something thats not in the text
        # sub_cost = penalty for typing something wrong
        for i in range(-1, len(needle)):
            current_row = [(i+1)*self.ins_cost]
            for j in range(0, len(haystack)):
                deletion = current_row[j] + self.del_cost
                if i == -1:
                    current_row.append(deletion)
                else:
                    insertion = previous_row[j + 1] + self.ins_cost
                    substitution = previous_row[j] + (needle[i] != haystack[j])*self.sub_cost
                    current_row.append(min(insertion, deletion, substitution))
            previous_row = current_row
        return previous_row[-1]
