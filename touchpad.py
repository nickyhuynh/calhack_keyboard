import math


def distance2(pos1, pos2):
    x_diff = pos1[0][0] - pos2[0][0]
    y_diff = pos1[0][1] - pos2[0][1]
    return x_diff * x_diff + y_diff * y_diff


def merge(pos1, pos2):
    return ((pos1[0][0] + pos2[0][0]) / 2, (pos1[0][1] + pos2[0][1]) / 2), pos1[1] + pos2[1]


class Hand:
    """ each finger has structure ((center_x, center_y), size) """
    def __init__(self, palm):
        self.palm = palm
        self.fingers = []
        self.thumb = None
        self.left = None  # whether this is the left hand
        self.dir = 0.0

    def add_finger(self, finger):
        self.fingers.append(finger)

    def formulate(self):
        # separates thumb from fingers and decides self.left
        self.fingers = sorted(self.fingers, key=lambda x: x[1], reverse=True)
        self.thumb = self.fingers.pop([0])
        self.fingers = sorted(self.fingers, key=lambda x: distance2(x, self.thumb))
        f_1 = self.fingers[0]
        f_34 = merge(self.fingers[3], self.fingers[4])
        self.dir = float(f_34[0][1] - f_1[0][1]), float(f_34[0][0] - f_1[0][0])
        dir_length = math.sqrt(self.dir[0] * self.dir[0] + self.dir[1] * self.dir[1])
        thumb_dir = float(self.thumb[0][1] - f_1[0][1]), float(self.thumb[0][0] - f_1[0][0])
        thumb_dir_length = math.sqrt(thumb_dir[0] * thumb_dir[0] + thumb_dir[1] * thumb_dir[1])
        dot_product = (self.dir[0] * thumb_dir[0] + self.dir[1] * thumb_dir[1])
        angle = math.acos(float(dot_product) / float(dir_length * thumb_dir_length))
        self.left = angle < 0


class Touchpad:
    def __init__(self):
        self.empty_image = []
        self.current_image = None
        self.current_map = None
        self.count = 0
        self.left = None
        self.right = None


    def process_image(self, image):
        self.current_image = image
        if self.count >= 10:
            fingers = sorted(self.get_fingers(), key=lambda x: x[1], reverse=True)
            if len(fingers) >= 12:
                self.separate_hands(fingers)
            else:
                pass

        else:
            self.empty_image.append(self.current_image)
            if self.count == 9:
                average = []
                for j in range(len(self.empty_image[0])):
                    average.append([])
                    for k in range(len(self.empty_image[0][j])):
                        average[j].append(sum(self.empty_image[i][j][k] for i in range(len(self.empty_image))) / 10)
                self.empty_image = average
            self.count += 1

    def get_fingers(self):
        # gets a 2D_list of booleans that represents finger presses
        hands_on = []
        for j in range(len(self.empty_image)):
            hands_on.append([])
            for k in range(len(self.empty_image[j])):
                hands_on[j].append(self.empty_image[j][k] - self.current_image[j][k] >= 40)
        print(hands_on)

        # gets an list of fingers of the structure ((center_x, center_y), size)
        segments = []
        mapping = {}
        for i in range(len(hands_on)):
            for j in range(len(hands_on[i])):
                if hands_on[i][j]:
                    mapped = False
                    directions = []
                    if i > 0:
                        if j > 0:
                            directions.append((-1, -1))
                        elif j < len(hands_on[i]) - 1:
                            directions.append((-1, 1))
                        directions.append((-1, 0))
                    if j > 0:
                        directions.append((0, -1))
                    for k in directions:
                        if not mapped and mapping.get((i + k[0], j + k[1])):
                            mapping[(i, j)] = mapping[(i + k[0], j + k[1])]
                            segments[mapping[(i + k[0], j + k[1])]].append((i, j))
                            mapped = True
                    if not mapped:
                        segments.append([(i, j)])
                        mapping[(i, j)] = len(segments) - 1
        for s in range(len(segments)):
            for (i, j) in segments[s]:
                unique = True
                directions = []
                if i < len(hands_on) - 1:
                    if j > 0:
                        directions.append((1, -1))
                    elif j < len(hands_on[i]) - 1:
                        directions.append((1, 1))
                    directions.append((1, 0))
                if j < len(hands_on[i]) - 1:
                    directions.append((0, 1))
                for t in range(len(segments)):
                    for k in directions:
                        if unique and t != s and (i + k[0], j + k[1]) in segments[t]:
                            segments[t] += segments[s]
                            unique = False
                if not unique:
                    segments[s] = []
        fingers = []
        for s in segments:
            if s:
                fingers.append((sorted(s, key=lambda x: x[1])[int(len(s) / 2)], len(s)))
        return fingers

    def separate_hands(self, fingers):
        # separate all fingers into two hands, different cases for 12 / 13 / 14 detected positions
        palm1, palm2 = None, None
        if len(fingers) == 12:
            palm1 = fingers[0]
            palm2 = fingers[1]
        elif len(fingers) == 13:
            d1 = distance2(fingers[0], fingers[1])
            d2 = distance2(fingers[0], fingers[2])
            d3 = distance2(fingers[1], fingers[2])
            ranking = sorted((d1, d2, d3))
            if ranking[0] == d1:
                palm1 = merge(fingers[0], fingers[1])
                palm2 = fingers[2]
            if ranking[0] == d2:
                palm1 = merge(fingers[0], fingers[2])
                palm2 = fingers[1]
            if ranking[0] == d3:
                palm1 = merge(fingers[1], fingers[2])
                palm2 = fingers[0]
            fingers.pop(2)
        elif len(fingers) == 14:
            d1 = distance2(fingers[0], fingers[1])
            d2 = distance2(fingers[0], fingers[2])
            d3 = distance2(fingers[0], fingers[3])
            d4 = distance2(fingers[1], fingers[2])
            d5 = distance2(fingers[1], fingers[3])
            d6 = distance2(fingers[2], fingers[3])
            ranking = sorted((d1 + d6, d2 + d5, d3 + d4))
            if ranking[0] == d1 + d6:
                palm1 = merge(fingers[0], fingers[1])
                palm2 = merge(fingers[2], fingers[3])
            if ranking[0] == d2 + d5:
                palm1 = merge(fingers[0], fingers[2])
                palm2 = merge(fingers[1], fingers[3])
            if ranking[0] == d3 + d4:
                palm1 = merge(fingers[0], fingers[3])
                palm2 = merge(fingers[1], fingers[2])
            fingers.pop(3)
            fingers.pop(2)
        fingers.pop(1)
        fingers.pop(0)
        hand1 = Hand(palm1)
        hand2 = Hand(palm2)
        for i in fingers:
            if distance2(i, hand1.palm) < distance2(i, hand2.palm):
                hand1.add_finger(i)
            else:
                hand2.add_finger(i)
        hand1.formulate()
        hand2.formulate()
        if hand1.left:
            self.left = hand1
            self.right = hand2
        else:
            self.left = hand2
            self.right = hand1

    def reset(self):
        self.empty_image = []
        self.current_image = None
        self.count = 0