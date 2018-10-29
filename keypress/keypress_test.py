#!/usr/bin/env python3

from keypress import KeyPress
import unittest

class TestKeyPress(unittest.TestCase):

    def setUp(self):
        pass

    def test_cat(self):
        f = []
        c = KeyPress.compile("A<A>.a<a>", A=lambda: f.append('A'), a=lambda: f.append('a'))

        key_press = KeyPress(c)
        key_press.process_input('A')
        key_press.process_input(12)
        key_press.process_input(13)
        key_press.process_input('a')
        self.assertEqual(['A', 'a'], f)
        self.assertEqual("match", key_press.status())

    def test_union(self):
        # A|a
        c = KeyPress.compile("A<A>|a<a>", A=lambda: f.append('A'), a=lambda: f.append('a'))
        
        f = []
        key_press = KeyPress(c)
        key_press.process_input('A')
        self.assertEqual(['A'], f)
        self.assertEqual("match", key_press.status())
    
        f = []
        key_press.reset()
        key_press.process_inputs(['a'])
        self.assertEqual(['a'], f)
        self.assertEqual("match", key_press.status())

    def test_star(self):
        # A*
        f = []
        c = KeyPress.compile("(A<A>)*", A=lambda: f.append('A'))
        
        key_press = KeyPress(c)
        key_press.process_inputs(['A', 'A'])
    
        self.assertEqual(['A', 'A'], f)
        self.assertEqual("match", key_press.status())

    def test_star2(self):
        # (Aa)*
        f = []
        c = KeyPress.compile("(A<A>a<a>)*", A=lambda: f.append('A'), a=lambda: f.append('a'))
        
        key_press = KeyPress(c)
        key_press.process_inputs(['A', 'a', 'A'])
        self.assertEqual(['A', 'a', 'A'], f)
        self.assertEqual("in progress", key_press.status())
    
        key_press.process_inputs(['a'])
        self.assertEqual(['A', 'a', 'A', 'a'], f)
        self.assertEqual("match", key_press.status())

    def test_composite(self):
        f = []
        #    A(bc|d)*a
        c = KeyPress.compile("A<A>(b<b>c<c>|d<dd>)*a<a>", A=lambda: f.append('A'), a=lambda: f.append('a'), b=lambda: f.append('b'), c=lambda: f.append('c'), dd=lambda: f.append('d'))
    
        key_press = KeyPress(c)
        self.assertEqual("in progress", key_press.status())
        key_press.process_input('A')
        self.assertEqual(['A'], f)
        self.assertEqual("in progress", key_press.status())
        key_press.process_input('b')
        self.assertEqual(['A', 'b'], f)
        self.assertEqual("in progress", key_press.status())
        key_press.process_input('c')
        self.assertEqual(['A', 'b', 'c'], f)
        self.assertEqual("in progress", key_press.status())
        key_press.process_input('a')
        self.assertEqual(['A', 'b', 'c', 'a'], f)
        self.assertEqual("match", key_press.status())

    def test_time(self):
        # A12-15<call>13-16*a
        c = KeyPress.compile("A<A>12-15<call>13-16*a<a>", A=lambda: f.append('A'), a=lambda: f.append('a'), call=lambda: f.append('12-15'))
        
        f = []
        key_press = KeyPress(c)
        self.assertEqual({12,15}, key_press.process_input('A'))
        self.assertEqual({12,15}, key_press.process_input(4))
        self.assertEqual({12,15}, key_press.process_input(8))
        self.assertEqual({13,16}, key_press.process_input(12))
        self.assertEqual({13,16}, key_press.process_input(13))
        self.assertEqual(set(), key_press.process_input('a'))
        self.assertEqual(['A', '12-15', 'a'], f)
        self.assertEqual("match", key_press.status())
    
        f = []
        key_press.reset()
        self.assertEqual("in progress", key_press.status())
        key_press.process_inputs(['A', 4, 8])
        self.assertEqual(['A'], f)
        self.assertEqual("in progress", key_press.status())
        key_press.process_inputs(['a'])
        self.assertEqual(['A'], f)
        self.assertEqual("failed", key_press.status())

        f = []
        key_press.reset()
        self.assertEqual("in progress", key_press.status())
        key_press.process_inputs(['A', 4, 13, 20])
        self.assertEqual(['A', '12-15'], f)
        self.assertEqual("failed", key_press.status())

    def test_time2(self):
        # Aa12-15*
        c = KeyPress.compile("Aa12-15*")
        
        f = []
        key_press = KeyPress(c)
        key_press.process_inputs(['A', 'a', 4, 8, 12, 13])
        self.assertEqual("match", key_press.status())

    def test_time3(self):
        c = KeyPress.compile(".C(.A100-300+a<one>|.A200-400+a<two>)*.c", one=lambda: f.append("one"), two=lambda: f.append("two"))
        f = []
        key_press = KeyPress(c)
        self.assertEqual(set(), key_press.process_input('C'))
        self.assertEqual({100,200,300,400}, key_press.process_input('A'))
        self.assertEqual({200,400}, key_press.process_input(350))
        self.assertEqual(set(), key_press.process_input('a'))
        self.assertEqual(set(), key_press.process_input('c'))
        self.assertEqual("match", key_press.status())
        self.assertEqual(['two'], f)

    def test_time4(self):
        c = KeyPress.compile(".C100-300<one>300-500<two>500-700<three>.c", one=lambda: f.append("one"), two=lambda: f.append("two"), three=lambda: f.append("three"))
        f = []
        key_press = KeyPress(c)
        self.assertEqual({100,300}, key_press.process_input('C'))
        self.assertEqual([], f)
        self.assertEqual({300,500}, key_press.process_input(200))
        self.assertEqual(['one'], f)
        self.assertEqual({500,700}, key_press.process_input(400))
        self.assertEqual(['one', 'two'], f)
        self.assertEqual(set(), key_press.process_input(600))
        self.assertEqual(['one', 'two', 'three'], f)
        self.assertEqual(set(), key_press.process_input('c'))
        self.assertEqual("match", key_press.status())

    def test_zero_or_one(self):
        # AB?C
        c = KeyPress.compile("A<A>(B<B>)?C<C>", A=lambda: f.append('A'), B=lambda: f.append('B'), C=lambda: f.append('C'))
    
        f = []
        key_press = KeyPress(c)
        key_press.process_inputs(['A'])
        self.assertEqual(['A'], f)
        self.assertEqual("in progress", key_press.status())
        key_press.process_inputs(['B'])
        self.assertEqual(['A', 'B'], f)
        self.assertEqual("in progress", key_press.status())
        key_press.process_inputs(['C'])
        self.assertEqual(['A', 'B', 'C'], f)
        self.assertEqual("match", key_press.status())

        f = []
        key_press.reset()
        key_press.process_inputs(['A'])
        self.assertEqual(['A'], f)
        self.assertEqual("in progress", key_press.status())
        key_press.process_inputs(['C'])
        self.assertEqual(['A', 'C'], f)
        self.assertEqual("match", key_press.status())
    
        f = []
        key_press.reset()
        key_press.process_inputs(['A'])
        self.assertEqual(['A'], f)
        self.assertEqual("in progress", key_press.status())
        key_press.process_inputs(['B'])
        self.assertEqual(['A', 'B'], f)
        self.assertEqual("in progress", key_press.status())
        key_press.process_inputs(['B'])
        self.assertEqual(['A', 'B'], f)
        self.assertEqual("failed", key_press.status())

    def test_any_order(self):
        #A&bc&D
        c = KeyPress.compile("A<A>&b<b>c<c>&D<D>", A=lambda: f.append('A'), b=lambda: f.append('b'), c=lambda: f.append('c'), D=lambda: f.append('D'))
    
        f = []
        key_press = KeyPress(c)
        key_press.process_inputs(['A'])
        self.assertEqual(['A'], f)
        self.assertEqual("in progress", key_press.status())
        key_press.process_inputs(['b', 'c'])
        self.assertEqual(['A', 'b', 'c'], f)
        self.assertEqual("in progress", key_press.status())
        key_press.process_inputs(['D'])
        self.assertEqual(['A', 'b', 'c', 'D'], f)
        self.assertEqual("match", key_press.status())
    
        f = []
        key_press.reset()
        key_press.process_inputs(['D'])
        self.assertEqual(['D'], f)
        self.assertEqual("in progress", key_press.status())
        key_press.process_inputs(['D'])
        self.assertEqual(['D'], f)
        self.assertEqual("failed", key_press.status())

        #------------------
        #test all combinations:
        f = []
        key_press.reset()
        key_press.process_inputs(['A', 'b', 'c', 'D'])
        self.assertEqual("match", key_press.status())
    
        f = []
        key_press.reset()
        key_press.process_inputs(['A', 'D', 'b', 'c'])
        self.assertEqual("match", key_press.status())
    
        f = []
        key_press.reset()
        key_press.process_inputs(['b', 'c', 'A', 'D'])
        self.assertEqual("match", key_press.status())
    
        f = []
        key_press.reset()
        key_press.process_inputs(['b', 'c', 'D', 'A'])
        self.assertEqual("match", key_press.status())
    
        f = []
        key_press.reset()
        key_press.process_inputs(['D', 'A', 'b', 'c'])
        self.assertEqual("match", key_press.status())
    
        f = []
        key_press.reset()
        key_press.process_inputs(['D', 'b', 'c', 'A'])
        self.assertEqual("match", key_press.status())
        #------------------
    
        f = []
        key_press.reset()
        key_press.process_inputs(['A', 'c', 'b', 'D'])
        self.assertEqual("failed", key_press.status())


    def test_count(self):
        #A{3,5}
        c = KeyPress.compile("A{3,5}", done=lambda: f.append('done'))
    
        f = []
        key_press = KeyPress(c)
        key_press.process_inputs(['A'])
        self.assertEqual([], f)
        self.assertEqual("in progress", key_press.status())
        key_press.process_inputs(['A'])
        self.assertEqual([], f)
        self.assertEqual("in progress", key_press.status())
        key_press.process_inputs(['A'])
        self.assertEqual([], f)
        self.assertEqual("match", key_press.status())
        key_press.process_inputs(['A'])
        self.assertEqual([], f)
        self.assertEqual("match", key_press.status())
        key_press.process_inputs(['A'])
        self.assertEqual([], f)
        self.assertEqual("match", key_press.status())
        key_press.process_inputs(['A'])
        self.assertEqual([], f)
        self.assertEqual("failed", key_press.status())

if __name__ == '__main__':
    unittest.main()
