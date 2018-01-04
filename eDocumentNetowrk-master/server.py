#!/usr/bin/python
'''
The server need to main two databases which are push_list and post_dict
and I just use dictionary post_dict to store all the posts
and use list push_list to store all the push client

post_dict format: { exupery_page1: [username > line_num > content > serial, ...], ...}

'''


from socket import *
import threading
import time
import os
import sys

# Add post record into post_dict
def add_record(page_line, content):
	global post_dict
	post_dict.setdefault(page_line, []).append(content)


# Format the post record into post_dict
def format_local_post_database(message):
	# page: exupery 1
	# content: line_num post
	# format_content = 'post_to_forum' + ' ' + username + ' ' + page + ' ' + \
	# 				content + serial_num
	global push_list
	global post_dict
	global push_list_socket

	post_record = ''
	string = message.split()
	username = string[1]
	bookname = string[2]
	page = string[3]
	line = string[4]
	content = ''

	for i in range(5, len(string)):
		content += string[i] + ' '

	book_page = bookname + '_page' + page
	post_record += username + ' > ' + line + ' > ' + content 
	serial_record = assgin_serial(post_record, book_page)
	add_record(book_page, serial_record)

	print 'New post received from :' + username

	serial_end = '(' + bookname + ',' + ' ' + page + ',' + ' ' + line + ',' + ' ' + serial_record.split(' > ')[3] + ')'  
	print 'Post added to the database and given serial number', serial_end

	# Forward the message to push client
	if len(push_list) != 0:
		for i in range(len(push_list_socket)):
			username = push_list[i].split('~')[5]
			push_reply = book_page + '~' + serial_record
			push_list_socket[i].send(push_reply)
			print username + ' is on push list and push message to ' + username 

	else:
		print 'Push list empty. No action required.'


# Assign the serial number with each post record
def assgin_serial(post_record, book_page):
	global post_dict

	if book_page in post_dict.keys():
		post_records = post_dict[book_page]
		line_num = []
		for record in post_records:
			num = record.split(' > ')[1]
			line_num.append(num)

		current_num = post_record.split(' > ')[1]
		assgin_serial = line_num.count(current_num) + 1

		return post_record + ' > ' + str(assgin_serial) + '\n'
	else:
		return post_record + ' > ' + str(1) + '\n'


# Send the book content along with associated posts to client
def read_send(socket, book_path, post_dict, username):
	#book_path = exupery_page1

	reply = ''
	file_path = book_path
	file_book = open(file_path)
	book_content = file_book.read()

	if book_path not in post_dict.keys():
		reply = book_content + '~' + book_path + '~' + 'null'
	else:
		post_content = format_post(book_path, post_dict)
		reply = book_content + '~' + book_path + '~' + post_content

	socket.send(reply)

	print 'Query is received from ' + username + ' for posts associated with page ' + \
			file_path.split('_page')[1] + ' of the book ' + file_path.split('_page')[0]


def format_post(book_path, post_dict):
	post_content = ''
	for i in range(len(post_dict[book_path])):
		post_content += post_dict[book_path][i]

	return post_content


# Put the push client info into push_list
# and create the corresponing socket into push_list_socket
def create_push_list(message):

	global push_list
	global post_dict
	global push_list_socket
	global push_ip

	push_list.append(message)

	message_arr = message.split('~')
	addr = message_arr[1]
	port = message_arr[2]
	unread = message_arr[3]
	readed = message_arr[4]
	username = message_arr[5]

	push_socket = 'push_socket_' + str(len(push_list))


	push_socket = socket(AF_INET, SOCK_STREAM)
	push_socket.connect((push_ip, int(port)))


	push_list_socket.append(push_socket)

	print 'Received a request from ' + username + "'s reader to work in push mode and \
			has added int to the 'push_list'"

	print 'Received the summary of ' + username + ' unread: ' + unread + ' readed: ' + readed  

	if len(post_dict) != 0:
		for book_page in post_dict.keys():
			for book_record in post_dict[book_page]:
				print 'Forwarded: ', book_page + '~' + book_record
				push_socket.send(book_page + '~' + book_record + '\n')


# Only send the book content in the push mode
def push_send(socket, book_path):

	file_path = book_path
	file_book = open(file_path)
	book_content = file_book.read()

	socket.send(book_content)



def interaction(connectionSocket, addr):

	global post_dict
	global push_ip
	print 'Get connection from: ', addr

	push_ip = addr[0]

	while 1:
			message = connectionSocket.recv(1024)
			if not message:
				break

			elif message.startswith('display'):
				command, book_path, username = message.split()
				read_send(connectionSocket, book_path, post_dict, username)

			elif message.startswith('post_to_forum'):
				post_record = format_local_post_database(message)

			elif message.startswith('push~'):
				create_push_list(message)

			elif message.startswith('push display'):
				message_arr = message.split()
				book_page = message_arr[2]
				push_send(connectionSocket, book_page)

	connectionSocket.close();


def main():

	serverPort = int(sys.argv[1])
	serverSocket = socket(AF_INET, SOCK_STREAM)
	serverSocket.bind(('', serverPort))
	serverSocket.listen(10)

	while 1:
		connectionSocket, addr = serverSocket.accept();
		thread = threading.Thread(target = interaction, args = (connectionSocket, addr))
		thread.start()

if __name__ == '__main__':

	post_dict = {}
	push_list = []
	push_list_socket = []
	main()








